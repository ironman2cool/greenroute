"""Device specs + Ollama detection. Used by the API (/setup) and setup.py."""
import os
import platform
import shutil
import subprocess
import time

import httpx
import psutil

import config

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
_WIN_OLLAMA = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe")


def _run(cmd: list[str], timeout: float = 5) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def detect_gpus() -> list[str]:
    gpus = _run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"]).splitlines()
    if gpus:
        return gpus
    system = platform.system()
    if system == "Windows":
        out = _run(["powershell", "-NoProfile", "-Command",
                    "(Get-CimInstance Win32_VideoController).Name"])
        return [l.strip() for l in out.splitlines() if l.strip()]
    if system == "Darwin":
        out = _run(["system_profiler", "SPDisplaysDataType"])
        return [l.split(":", 1)[1].strip() for l in out.splitlines() if "Chipset Model" in l]
    return []


def system_specs() -> dict:
    battery = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
    return {
        "os": f"{platform.system()} {platform.release()}",
        "cpu": platform.processor() or platform.machine(),
        "cpu_cores": psutil.cpu_count(logical=False) or psutil.cpu_count(),
        "ram_gb": round(psutil.virtual_memory().total / 1024**3, 1),
        "ram_free_gb": round(psutil.virtual_memory().available / 1024**3, 1),
        "disk_free_gb": round(shutil.disk_usage(os.path.expanduser("~")).free / 1024**3, 1),
        "gpus": detect_gpus(),
        "battery_pct": battery.percent if battery else None,
        "on_battery": (not battery.power_plugged) if battery else False,
    }


def live_specs() -> dict:
    """The cheap, fast-changing readings the router checks on every request (no GPU probe)."""
    battery = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
    return {
        "ram_free_gb": round(psutil.virtual_memory().available / 1024**3, 1),
        "battery_pct": battery.percent if battery else None,
        "on_battery": (not battery.power_plugged) if battery else False,
    }


def recommend_model(specs: dict) -> dict:
    """Pick by total RAM, but step down when little is free: a 3B model on a machine with
    2 GB free pages to disk and becomes slower than the cloud round trip it was meant to save."""
    ram, free = specs["ram_gb"], specs.get("ram_free_gb", specs["ram_gb"])
    if ram < 4:
        return {"model": None, "size_gb": 0, "why": f"{ram} GB RAM is too little for a local LLM - cloud only."}
    if ram < 8 or free < 3:
        return {"model": "llama3.2:1b", "size_gb": 1.3,
                "why": f"{ram} GB RAM ({free} GB free) - the 1B model fits comfortably."}
    return {"model": "llama3.2:3b", "size_gb": 2.0,
            "why": f"{ram} GB RAM ({free} GB free) - the 3B model is a good speed/quality balance."}


def ollama_binary() -> str | None:
    found = shutil.which("ollama")
    if found:
        return found
    if platform.system() == "Windows" and os.path.exists(_WIN_OLLAMA):
        return _WIN_OLLAMA
    return None


def _ollama_get(path: str) -> list[dict] | None:
    try:
        r = httpx.get(f"{config.OLLAMA_URL}{path}", timeout=2)
        r.raise_for_status()
        return r.json().get("models", [])
    except (httpx.HTTPError, ValueError):
        return None


def ollama_models() -> list[str] | None:
    """Installed model names, or None if the server isn't responding."""
    tags = _ollama_get("/api/tags")
    return None if tags is None else [m["name"] for m in tags]


def loaded_models() -> list[str]:
    """Models Ollama currently holds in memory (they need no extra RAM to answer)."""
    return [m["name"] for m in (_ollama_get("/api/ps") or [])]


def _has_model(models: list[str], wanted: str) -> bool:
    return any(m == wanted or m == f"{wanted}:latest" for m in models)


def _params_b(size: str | None) -> float | None:
    """'1.2B' -> 1.2, '7.2B' -> 7.2, '500M' -> 0.5"""
    try:
        return float(size[:-1]) / (1000 if size.upper().endswith("M") else 1)
    except (TypeError, ValueError):
        return None


def ollama_status() -> dict:
    binary = ollama_binary()
    tags = _ollama_get("/api/tags")
    models = None if tags is None else [m["name"] for m in tags]
    running = models is not None
    ready = running and _has_model(models, config.LOCAL_MODEL)
    info = next((m for m in tags or [] if m["name"] in (config.LOCAL_MODEL, f"{config.LOCAL_MODEL}:latest")), {})
    if ready:
        msg = f"Local model {config.LOCAL_MODEL} is ready."
    elif running:
        msg = f"Ollama is running but {config.LOCAL_MODEL} isn't downloaded (run: ollama pull {config.LOCAL_MODEL})."
    elif binary:
        msg = "Ollama is installed but not running (start the Ollama app, or run: ollama serve)."
    else:
        msg = "Ollama is not installed - no local model available."
    return {
        "installed": binary is not None or running,
        "binary": binary,
        "running": running,
        "models": models or [],
        "model": config.LOCAL_MODEL,
        "model_ready": ready,
        "loaded": ready and _has_model(loaded_models(), config.LOCAL_MODEL),
        "model_params_b": _params_b(info.get("details", {}).get("parameter_size")),
        "model_size_gb": round(info["size"] / 1e9, 1) if info.get("size") else None,
        "message": msg,
    }


_cache: dict = {"t": 0.0, "status": None}


def ollama_status_cached(ttl: float = 10) -> dict:
    """Per-request check without paying a 2 s timeout on every call."""
    if _cache["status"] is None or time.time() - _cache["t"] > ttl:
        _cache.update(t=time.time(), status=ollama_status())
    return _cache["status"]


def install_instructions() -> list[str]:
    system = platform.system()
    if system == "Windows":
        return [
            "Option A: winget install Ollama.Ollama",
            "Option B: download the installer from https://ollama.com/download/windows and run it",
            "Then open a NEW terminal so 'ollama' is on your PATH",
        ]
    if system == "Darwin":
        return ["brew install ollama   (or download from https://ollama.com/download/mac)"]
    return ["curl -fsSL https://ollama.com/install.sh | sh"]


def start_ollama(binary: str, wait_s: int = 15) -> bool:
    """Launch 'ollama serve' detached; True once the API answers."""
    kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if platform.system() == "Windows":
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen([binary, "serve"], **kwargs)
    for _ in range(wait_s):
        time.sleep(1)
        if ollama_models() is not None:
            return True
    return False


def set_env(key: str, value: str) -> None:
    """Persist a setting to .env so it survives restarts."""
    lines = open(ENV_PATH).read().splitlines() if os.path.exists(ENV_PATH) else []
    lines = [l for l in lines if not l.startswith(f"{key}=")] + [f"{key}={value}"]
    with open(ENV_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")
