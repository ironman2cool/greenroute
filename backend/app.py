"""GreenRoute backend: prompt -> route decision -> local or cloud inference -> impact estimate."""
import json
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Iterator, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

import cloud_backend
import config
import local_backend
import metrics
import model_manager
import router
import system_check


@asynccontextmanager
async def lifespan(_app: FastAPI):
    s = system_check.ollama_status_cached(ttl=0)
    print(f"\n[GreenRoute] Local: {s['message']}")
    if not s["model_ready"]:
        print(f"[GreenRoute] Local requests will fall back to cloud ({config.CLOUD_MODEL}). "
              "Run 'python setup_local.py' to set up a local model.\n")
    yield


app = FastAPI(title="GreenRoute", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class Device(BaseModel):
    """Client-side hints. They override the server's own readings, e.g. for demos."""
    low_spec: Optional[bool] = None
    battery_pct: Optional[float] = None
    on_battery: Optional[bool] = None


class ChatRequest(BaseModel):
    prompt: str = Field(max_length=50_000)
    route: Literal["auto", "local", "cloud"] = "auto"
    device: Optional[Device] = None


class PullRequest(BaseModel):
    model: Optional[str] = None  # defaults to the recommendation for this device


IMAGE_NOTICE = ("No image model is configured, so the cloud text model will answer in words "
                "instead of drawing an image.")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html",
                        headers={"Cache-Control": "no-cache"})


@app.get("/health")
def health():
    return {"ok": True, "local": system_check.ollama_status_cached(), "cloud_model": config.CLOUD_MODEL}


@app.get("/setup")
def setup():
    """Specs + local-model status + install steps, for the UI's device panel."""
    specs = system_check.system_specs()
    status = system_check.ollama_status_cached(ttl=0)
    return {
        "specs": specs,
        "recommended": system_check.recommend_model(specs),
        "local": status,
        "capability": router.model_capability(status.get("model_params_b")),
        "install_steps": [] if status["installed"] else system_check.install_instructions(),
    }


@app.post("/local/pull")
def pull_model(req: PullRequest):
    """Start downloading a local model (runs in the background)."""
    model = req.model or system_check.recommend_model(system_check.system_specs())["model"]
    if not model:
        raise HTTPException(400, "This device doesn't have enough RAM for a local model.")
    try:
        return model_manager.start_pull(model)
    except ValueError as e:
        raise HTTPException(409, {"message": str(e), "install_steps": system_check.install_instructions()})


@app.get("/local/pull")
def pull_progress():
    return model_manager.progress()


@app.post("/local/use")
def use_model(req: PullRequest):
    """Switch to a model that's already installed in Ollama (no download)."""
    installed = system_check.ollama_status()["models"]
    if req.model not in installed:
        raise HTTPException(404, f"{req.model} isn't installed. Installed: {', '.join(installed) or 'none'}")
    config.LOCAL_MODEL = req.model
    system_check.set_env("LOCAL_MODEL", req.model)
    system_check._cache["status"] = None
    return system_check.ollama_status_cached()


@app.get("/stats")
def get_stats():
    return {**metrics.stats(), "sources": metrics.SOURCES,
            "assumptions": {"device_active_watts": config.DEVICE_ACTIVE_WATTS,
                            "grid_gco2_per_kwh": config.GRID_GCO2_PER_KWH}}


@app.post("/stats/reset")
def reset_stats():
    return metrics.reset()


def _decide(req: ChatRequest) -> router.RouteDecision:
    force = None if req.route == "auto" else req.route
    device = req.device.model_dump(exclude_none=True) if req.device else {}
    d = router.decide(req.prompt, force=force, device=device,
                      local_status=system_check.ollama_status_cached(), specs=system_check.live_specs())
    if d.decision == "cloud" and d.details.get("classification", {}).get("task") == "image" and not d.notice:
        d.notice = IMAGE_NOTICE
    return d


@app.post("/route")
def route_only(req: ChatRequest):
    """Decision without inference - used by the UI's live route preview and for testing."""
    return _decide(req).to_dict()


def _prompt_for(d: router.RouteDecision, prompt: str) -> str:
    """Text models return nothing for 'draw me X'; ask for a description instead."""
    if d.details.get("classification", {}).get("task") == "image":
        return ("The user asked for an image, but only a text model is available. In one sentence say you "
                "can't draw images here, then describe the requested image vividly in 2-3 sentences.\n\n"
                f"Request: {prompt}")
    return prompt


def _finish(served: str, seconds: float, inp: int, out: int) -> dict:
    impact = metrics.estimate(served, seconds)
    return {"impact": impact, "stats": metrics.record(served, impact, inp, out)}


@app.post("/chat")
def chat(req: ChatRequest):
    if not req.prompt.strip():
        raise HTTPException(400, "Empty prompt")

    decision = _decide(req)
    simulated = False
    t0 = time.perf_counter()

    try:
        if decision.decision == "local":
            try:
                result = local_backend.generate(req.prompt, decision.model)
            except local_backend.LocalUnavailable as e:
                system_check._cache["status"] = None  # force re-check next request
                if config.LOCAL_UNAVAILABLE == "error":
                    raise HTTPException(503, str(e))
                if config.LOCAL_UNAVAILABLE == "simulate":
                    result = cloud_backend.generate(req.prompt, config.SIMULATED_LOCAL_MODEL)
                    simulated = True
                else:
                    decision = router.no_local_fallback(decision.reason, str(e), decision.details)
                    result = cloud_backend.generate(req.prompt, decision.model)
        else:
            result = cloud_backend.generate(_prompt_for(decision, req.prompt), decision.model)
    except cloud_backend.CloudError as e:
        raise HTTPException(502, str(e))

    seconds = time.perf_counter() - t0
    served = "cloud" if simulated else decision.decision  # simulated answers really ran in the cloud
    if result.get("note"):
        decision.notice = " ".join(filter(None, [decision.notice, result["note"] + "."]))
    return {
        **decision.to_dict(),
        "model": result["model"],
        "simulated": simulated,
        "response": result["text"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "latency_ms": round(seconds * 1000),
        **_finish(served, seconds, result["input_tokens"], result["output_tokens"]),
    }


def _events(req: ChatRequest) -> Iterator[str]:
    """NDJSON events: decision -> token* -> [fallback -> token*] -> done | error."""
    line = lambda obj: json.dumps(obj) + "\n"
    decision = _decide(req)
    yield line({"type": "decision", **decision.to_dict()})

    t0 = time.perf_counter()
    ttft, usage, simulated, emitted = None, {}, False, False

    def pump(events):
        nonlocal ttft, usage, emitted
        for ev in events:
            if ev["type"] == "token":
                ttft = ttft or time.perf_counter() - t0
                emitted = True
                yield line(ev)
            elif ev["type"] == "note":
                yield line(ev)
            else:
                usage = ev

    try:
        if decision.decision == "local":
            try:
                yield from pump(local_backend.stream(req.prompt, decision.model))
            except local_backend.LocalUnavailable as e:
                system_check._cache["status"] = None
                if config.LOCAL_UNAVAILABLE == "error":
                    yield line({"type": "error", "detail": str(e)})
                    return
                if config.LOCAL_UNAVAILABLE == "simulate":
                    simulated, model = True, config.SIMULATED_LOCAL_MODEL
                else:
                    decision = router.no_local_fallback(decision.reason, str(e), decision.details)
                    model = decision.model
                yield line({"type": "fallback", "reset": emitted, "simulated": simulated, **decision.to_dict()})
                yield from pump(cloud_backend.stream(req.prompt, model))
        else:
            yield from pump(cloud_backend.stream(_prompt_for(decision, req.prompt), decision.model))
    except cloud_backend.CloudError as e:
        yield line({"type": "error", "detail": str(e)})
        return

    seconds = time.perf_counter() - t0
    served = "cloud" if simulated else decision.decision
    inp, out = usage.get("input_tokens", 0), usage.get("output_tokens", 0)
    yield line({
        "type": "done", "decision": decision.decision, "model": usage.get("model", decision.model),
        "simulated": simulated, "input_tokens": inp, "output_tokens": out,
        "latency_ms": round(seconds * 1000), "ttft_ms": round((ttft or seconds) * 1000),
        **_finish(served, seconds, inp, out),
    })


@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    if not req.prompt.strip():
        raise HTTPException(400, "Empty prompt")
    return StreamingResponse(_events(req), media_type="application/x-ndjson")
