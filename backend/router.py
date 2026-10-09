"""Routing decision engine: classify -> check device -> decide local or cloud.

decide() returns a RouteDecision. The first four fields are the stable contract the
rest of the app relies on; `details` carries the evidence for the UI's "why" panel.
"""
from dataclasses import dataclass, asdict, field
from typing import Literal, Optional

import config
from classifier import Classification, classify

Decision = Literal["local", "cloud"]


@dataclass
class RouteDecision:
    decision: Decision
    model: str
    reason: str
    notice: Optional[str] = None  # user-facing banner, e.g. "no local model"
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def model_capability(params_b: Optional[float]) -> float:
    """Highest prompt complexity a local model of this size handles well (calibrated on the
    benchmark in benchmark/). Unknown size -> treat it like a small model."""
    if params_b is None or params_b <= 1.5:
        return 0.35
    if params_b <= 4:
        return 0.5
    if params_b <= 9:
        return 0.6
    return 0.7


def model_ram_gb(local_status: Optional[dict]) -> float:
    """RAM needed to load the model: weights plus ~20% for context/KV cache."""
    size = (local_status or {}).get("model_size_gb") or 1.3
    return round(size * 1.2 + 0.3, 1)


def no_local_fallback(reason: str, local_msg: str, details: Optional[dict] = None) -> RouteDecision:
    return RouteDecision(
        "cloud", config.CLOUD_MODEL,
        f"{reason} -> no local model available, routed to cloud",
        notice=f"No local model available: {local_msg} Using cloud instead.",
        details=details or {},
    )


def _checks(c: Classification, device: dict, specs: dict, local_status: Optional[dict]) -> list[dict]:
    """Every check the router makes, in priority order. The first failing one decides."""
    status = local_status or {}
    model = config.LOCAL_MODEL
    cap = model_capability(status.get("model_params_b"))
    battery = device.get("battery_pct", specs.get("battery_pct"))  # None on desktops
    unplugged = device.get("on_battery", specs.get("on_battery", False))
    pct = "?" if battery is None else f"{battery:g}"
    free = specs.get("ram_free_gb")
    need = model_ram_gb(status)
    loaded = status.get("loaded", False)

    def chk(name, ok, detail, why_cloud):
        return {"name": name, "ok": bool(ok), "detail": detail, "why_cloud": why_cloud}

    return [
        chk("Task type", c.task != "image", c.label,
            "Image generation can't run on a local text model"),
        chk("Device mode", not device.get("low_spec"),
            "low-spec mode" if device.get("low_spec") else "normal",
            "Low-spec device: on-device inference would be too slow"),
        chk("Battery", not (unplugged and battery is not None and battery < config.LOW_BATTERY_PCT),
            "plugged in" if not unplugged else f"{pct}% on battery",
            f"Battery at {pct}% and unplugged: offloading to save power"),
        chk("Input length", c.input_tokens <= config.LOCAL_MAX_INPUT_TOKENS,
            f"~{c.input_tokens:,} tokens (limit {config.LOCAL_MAX_INPUT_TOKENS:,})",
            f"Input of ~{c.input_tokens:,} tokens is too long for fast on-device inference"),
        chk("Confidence", not (c.task == "unknown" and c.complexity >= config.UNKNOWN_CLOUD_COMPLEXITY),
            f"{c.confidence:.0%}",
            "Couldn't classify this request confidently, so using the cloud to be safe"),
        chk("Complexity", c.complexity <= cap, f"{c.complexity:.2f} vs {model} limit {cap:.2f}",
            f"{c.label} (complexity {c.complexity:.2f}) is beyond what {model} handles well (limit {cap:.2f})"),
        chk("Memory", loaded or free is None or free >= need,
            "model already loaded" if loaded else f"{free} GB free, needs ~{need} GB",
            f"Only {free} GB RAM free; {model} needs ~{need} GB"),
    ]


def decide(prompt: str, force: Optional[Decision] = None, device: Optional[dict] = None,
           local_status: Optional[dict] = None, specs: Optional[dict] = None) -> RouteDecision:
    c = classify(prompt)
    checks = _checks(c, device or {}, specs or {}, local_status)
    details = {"classification": c.to_dict(), "checks": checks}

    if force == "cloud":
        return RouteDecision("cloud", config.CLOUD_MODEL, "Forced cloud by client", details=details)

    if force == "local":
        d = RouteDecision("local", config.LOCAL_MODEL, "Forced local by client", details=details)
    else:
        failed = next((ch for ch in checks if not ch["ok"]), None)
        if failed:
            return RouteDecision("cloud", config.CLOUD_MODEL, failed["why_cloud"], details=details)
        d = RouteDecision("local", config.LOCAL_MODEL,
                          f"{c.label} (complexity {c.complexity:.2f}) is within {config.LOCAL_MODEL}'s range: "
                          "answered on-device", details=details)

    ready = local_status is None or local_status["model_ready"]
    if not ready and config.LOCAL_UNAVAILABLE == "cloud":
        return no_local_fallback(d.reason, local_status["message"], details)
    return d
