import os

from dotenv import load_dotenv

load_dotenv()


def _f(name: str, default: float) -> float:
    return float(os.getenv(name, default))


# --- Local inference (Ollama) ---
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LOCAL_MODEL = os.getenv("LOCAL_MODEL", "llama3.2:1b")
LOCAL_TIMEOUT_S = _f("LOCAL_TIMEOUT_S", 120)
# What to do when no local model is available:
#   "cloud"    - route to CLOUD_MODEL and show a notice (default)
#   "simulate" - tiny cloud model labelled as local, flagged simulated=true
#   "error"    - return 503
LOCAL_UNAVAILABLE = os.getenv("LOCAL_UNAVAILABLE", "cloud")
SIMULATED_LOCAL_MODEL = os.getenv("SIMULATED_LOCAL_MODEL", "gemini-3.5-flash-lite")

# --- Cloud inference (Gemini) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
CLOUD_MODEL = os.getenv("CLOUD_MODEL", "gemini-2.5-flash")
# Tried in order when the model above is out of free quota, overloaded or retired.
CLOUD_FALLBACK_MODELS = [m.strip() for m in os.getenv(
    "CLOUD_FALLBACK_MODELS", "gemini-3.5-flash-lite,gemini-flash-lite-latest,gemma-4-26b-a4b-it").split(",") if m.strip()]
CLOUD_MAX_TOKENS = int(os.getenv("CLOUD_MAX_TOKENS", "4096"))

SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "You are a helpful, concise assistant.")

# --- Router (Phase 2) ---
# Prompts above this many input tokens go to the cloud: long contexts are slow on laptop CPUs.
LOCAL_MAX_INPUT_TOKENS = int(os.getenv("LOCAL_MAX_INPUT_TOKENS", "1500"))
# Below this battery % (while unplugged) the router offloads to save the user's battery.
LOW_BATTERY_PCT = _f("LOW_BATTERY_PCT", 20)
# Unclassified prompts at or above this complexity go to the cloud ("when unsure, be safe").
UNKNOWN_CLOUD_COMPLEXITY = _f("UNKNOWN_CLOUD_COMPLEXITY", 0.3)

# --- Impact estimates (Phase 3) - see metrics.py for sources ---
# Extra power the device draws while generating (watts). ~25 W fits a laptop CPU under load;
# use ~10 W for Apple silicon or ~150-300 W for a desktop GPU.
DEVICE_ACTIVE_WATTS = _f("DEVICE_ACTIVE_WATTS", 25)
# Carbon intensity of the local electricity grid (gCO2e per kWh). Default: world average 2025.
GRID_GCO2_PER_KWH = _f("GRID_GCO2_PER_KWH", 458)

DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
