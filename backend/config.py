import os

from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LOCAL_MODEL = os.getenv("LOCAL_MODEL", "llama3.2:3b")
LOCAL_TIMEOUT_S = float(os.getenv("LOCAL_TIMEOUT_S", "120"))
# What to do when no local model is available:
#   "cloud"    - route to CLOUD_MODEL and show a notice (default)
#   "simulate" - tiny cloud model labelled as local, flagged simulated=true
#   "error"    - return 503
LOCAL_UNAVAILABLE = os.getenv("LOCAL_UNAVAILABLE", "cloud")
SIMULATED_LOCAL_MODEL = os.getenv("SIMULATED_LOCAL_MODEL", "gemini-2.5-flash-lite")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
CLOUD_MODEL = os.getenv("CLOUD_MODEL", "gemini-2.5-flash")
CLOUD_MAX_TOKENS = int(os.getenv("CLOUD_MAX_TOKENS", "4096"))

SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "You are a helpful, concise assistant.")
