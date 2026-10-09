import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402

# A typical healthy local setup: llama3.2:1b installed, loaded, plenty of RAM.
READY = {"installed": True, "binary": "ollama", "running": True, "models": ["llama3.2:1b"],
         "model": "llama3.2:1b", "model_ready": True, "loaded": True,
         "model_params_b": 1.2, "model_size_gb": 1.3, "message": "Local model llama3.2:1b is ready."}
NOT_INSTALLED = {**READY, "installed": False, "running": False, "models": [], "model_ready": False,
                 "loaded": False, "model_params_b": None, "model_size_gb": None,
                 "message": "Ollama is not installed - no local model available."}
SPECS = {"ram_free_gb": 6.0, "battery_pct": 80, "on_battery": False}


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    """Every test gets its own stats file and a known model name/fallback mode."""
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(config, "LOCAL_MODEL", "llama3.2:1b")
    monkeypatch.setattr(config, "LOCAL_UNAVAILABLE", "cloud")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "test-key")
