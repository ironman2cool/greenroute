"""GreenRoute backend: prompt -> route decision -> local or cloud inference."""
import time
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import cloud_backend
import config
import local_backend
import model_manager
import router
import system_check

app = FastAPI(title="GreenRoute")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ChatRequest(BaseModel):
    prompt: str
    route: Literal["auto", "local", "cloud"] = "auto"
    device: Optional[dict] = None  # Phase 2: {ram_gb, gpu, battery, low_spec, ...}


@app.on_event("startup")
def banner():
    s = system_check.ollama_status_cached(ttl=0)
    print(f"\n[GreenRoute] Local: {s['message']}")
    if not s["model_ready"]:
        print(f"[GreenRoute] Local requests will fall back to cloud ({config.CLOUD_MODEL}). "
              "Run 'python setup_local.py' to set up a local model.\n")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html",
                        headers={"Cache-Control": "no-cache"})


@app.get("/health")
def health():
    return {"ok": True, "local": system_check.ollama_status_cached(), "cloud_model": config.CLOUD_MODEL}


@app.get("/setup")
def setup():
    """Specs + local-model status + install steps, for a setup panel in the UI."""
    specs = system_check.system_specs()
    status = system_check.ollama_status_cached(ttl=0)
    return {
        "specs": specs,
        "recommended": system_check.recommend_model(specs),
        "local": status,
        "install_steps": [] if status["installed"] else system_check.install_instructions(),
    }


class PullRequest(BaseModel):
    model: Optional[str] = None  # defaults to the recommendation for this device


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


def _decide(req: ChatRequest) -> router.RouteDecision:
    force = None if req.route == "auto" else req.route
    return router.decide(req.prompt, force=force, device=req.device,
                         local_status=system_check.ollama_status_cached())


@app.post("/route")
def route_only(req: ChatRequest):
    """Decision without inference - handy for the UI to preview the route."""
    return _decide(req).to_dict()


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
                    decision = router.no_local_fallback(decision.reason, str(e))
                    result = cloud_backend.generate(req.prompt, decision.model)
        else:
            result = cloud_backend.generate(req.prompt, decision.model)
    except cloud_backend.CloudError as e:
        raise HTTPException(502, str(e))

    return {
        **decision.to_dict(),
        "model": result["model"],
        "simulated": simulated,
        "response": result["text"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "latency_ms": round((time.perf_counter() - t0) * 1000),
    }
