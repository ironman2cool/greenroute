"""Background download of a local model through Ollama, with progress for the UI."""
import json
import threading

import httpx

import config
import system_check as sc

_lock = threading.Lock()
_state = {"state": "idle", "model": None, "status": "", "pct": 0, "error": None}


def progress() -> dict:
    return dict(_state)


def _set(**kw) -> None:
    _state.update(kw)


def start_pull(model: str) -> dict:
    """Kick off a download. Returns the initial state, or raises ValueError if impossible."""
    status = sc.ollama_status()
    if not status["installed"]:
        raise ValueError("Ollama is not installed")
    with _lock:
        if _state["state"] in ("starting", "pulling"):
            return progress()
        _set(state="starting", model=model, status="Starting Ollama…", pct=0, error=None)
    threading.Thread(target=_run, args=(model, status), daemon=True).start()
    return progress()


def _run(model: str, status: dict) -> None:
    try:
        if not status["running"] and not sc.start_ollama(status["binary"]):
            raise RuntimeError("Ollama didn't start. Open the Ollama app, or run 'ollama serve' in a terminal.")

        _set(state="pulling", status="Connecting…")
        with httpx.stream("POST", f"{config.OLLAMA_URL}/api/pull",
                          json={"model": model, "name": model, "stream": True}, timeout=None) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line:
                    continue
                msg = json.loads(line)
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                total, done = msg.get("total"), msg.get("completed")
                if total and done:
                    _set(pct=round(done / total * 100))
                _set(status=msg.get("status", ""))

        # Make the new model the active local model, now and after restarts.
        config.LOCAL_MODEL = model
        sc.set_env("LOCAL_MODEL", model)
        sc._cache["status"] = None
        _set(state="done", status="Ready", pct=100)
    except Exception as e:  # surface any failure to the UI
        _set(state="error", error=str(e) or type(e).__name__)
