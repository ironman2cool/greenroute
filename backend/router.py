"""Routing decision engine.

Phase 1: forced routes + local-first default, with automatic cloud fallback
when no local model is available. Phase 2 replaces the auto branch with the
real classify -> device-check -> decide heuristics.
The output contract is stable: {decision, model, reason, notice}.
"""
from dataclasses import dataclass, asdict
from typing import Literal, Optional

import config

Decision = Literal["local", "cloud"]


@dataclass
class RouteDecision:
    decision: Decision
    model: str
    reason: str
    notice: Optional[str] = None  # user-facing banner, e.g. "no local model"

    def to_dict(self) -> dict:
        return asdict(self)


def no_local_fallback(reason: str, local_msg: str) -> RouteDecision:
    return RouteDecision(
        "cloud", config.CLOUD_MODEL,
        f"{reason} -> no local model available, routed to cloud",
        notice=f"No local model available: {local_msg} Using cloud instead.",
    )


def decide(prompt: str, force: Optional[Decision] = None, device: Optional[dict] = None,
           local_status: Optional[dict] = None) -> RouteDecision:
    if force == "cloud":
        return RouteDecision("cloud", config.CLOUD_MODEL, "Forced cloud by client")

    if force == "local":
        d = RouteDecision("local", config.LOCAL_MODEL, "Forced local by client")
    else:
        # Phase 1 placeholder: local-first default. Phase 2 heuristics go here.
        d = RouteDecision("local", config.LOCAL_MODEL, "Default: local-first (router heuristics pending)")

    ready = local_status is None or local_status["model_ready"]
    if not ready and config.LOCAL_UNAVAILABLE == "cloud":
        return no_local_fallback(d.reason, local_status["message"])
    return d
