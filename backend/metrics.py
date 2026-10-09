"""Energy, water and carbon estimates per request, plus running totals.

These are estimates, not measurements. Every constant is cited so a reader can check it.

Cloud baseline (per prompt) - Google, "Measuring the environmental impact of AI inference",
Aug 22 2025 (https://cloud.google.com/blog/products/infrastructure/measuring-the-environmental-impact-of-ai-inference,
paper: https://arxiv.org/abs/2508.15734). The median Gemini Apps text prompt uses 0.24 Wh,
emits 0.03 gCO2e and consumes 0.26 mL of water. The boundary is wide: accelerators, host
CPU/DRAM, idle reserve capacity and data-centre overhead (PUE). Water is data-centre cooling.

Local estimate - measured generation time x the device's extra power draw while generating
(config.DEVICE_ACTIVE_WATTS, default 25 W for a laptop CPU). Carbon uses the local grid's
intensity (config.GRID_GCO2_PER_KWH, default 458 g/kWh = world average 2025, Ember via
Our World in Data: https://ourworldindata.org/grapher/carbon-intensity-electricity).
Local inference uses no data-centre cooling water. Water used by power plants is left out
on both sides, so the comparison stays like-for-like.
"""
import json
import os
import threading

import config

CLOUD_WH_PER_PROMPT = 0.24
CLOUD_GCO2E_PER_PROMPT = 0.03
CLOUD_WATER_ML_PER_PROMPT = 0.26

SOURCES = [
    {"what": "Cloud energy, carbon and water per median text prompt (0.24 Wh, 0.03 gCO2e, 0.26 mL)",
     "url": "https://cloud.google.com/blog/products/infrastructure/measuring-the-environmental-impact-of-ai-inference"},
    {"what": "Grid carbon intensity, world average 2025 (458 gCO2/kWh)",
     "url": "https://ourworldindata.org/grapher/carbon-intensity-electricity"},
]


def cloud_footprint() -> dict:
    return {"wh": CLOUD_WH_PER_PROMPT, "gco2e": CLOUD_GCO2E_PER_PROMPT, "water_ml": CLOUD_WATER_ML_PER_PROMPT}


def local_footprint(seconds: float) -> dict:
    wh = config.DEVICE_ACTIVE_WATTS * seconds / 3600
    return {"wh": wh, "gco2e": wh * config.GRID_GCO2_PER_KWH / 1000, "water_ml": 0.0}


def estimate(decision: str, seconds: float) -> dict:
    """Footprint of this request vs the all-cloud baseline. `saved` can be negative: a slow
    local answer on a power-hungry device can cost more energy than the cloud would have."""
    actual = local_footprint(seconds) if decision == "local" else cloud_footprint()
    baseline = cloud_footprint()
    saved = {k: baseline[k] - actual[k] for k in baseline}
    r = lambda d: {k: round(v, 5) for k, v in d.items()}
    return {"actual": r(actual), "baseline": r(baseline), "saved": r(saved)}


# ---- Running totals, persisted so the counters survive restarts -------------------------
_lock = threading.Lock()
_EMPTY = {"requests": 0, "local": 0, "cloud": 0, "input_tokens": 0, "output_tokens": 0,
          "baseline": {"wh": 0.0, "gco2e": 0.0, "water_ml": 0.0},
          "actual": {"wh": 0.0, "gco2e": 0.0, "water_ml": 0.0}}


def _path() -> str:
    return os.path.join(config.DATA_DIR, "stats.json")


def _load() -> dict:
    try:
        with open(_path()) as f:
            return json.load(f)
    except (OSError, ValueError):
        return json.loads(json.dumps(_EMPTY))


def _with_saved(s: dict) -> dict:
    s = dict(s)
    s["saved"] = {k: round(s["baseline"][k] - s["actual"][k], 4) for k in s["baseline"]}
    s["local_share"] = round(s["local"] / s["requests"], 3) if s["requests"] else 0.0
    return s


def stats() -> dict:
    with _lock:
        return _with_saved(_load())


def record(decision: str, impact: dict, input_tokens: int, output_tokens: int) -> dict:
    with _lock:
        s = _load()
        s["requests"] += 1
        s[decision] += 1
        s["input_tokens"] += input_tokens
        s["output_tokens"] += output_tokens
        for side in ("baseline", "actual"):
            for k, v in impact[side].items():
                s[side][k] = round(s[side][k] + v, 6)
        os.makedirs(config.DATA_DIR, exist_ok=True)
        with open(_path(), "w") as f:
            json.dump(s, f, indent=1)
        return _with_saved(s)


def reset() -> dict:
    with _lock:
        try:
            os.remove(_path())
        except OSError:
            pass
        return _with_saved(_load())
