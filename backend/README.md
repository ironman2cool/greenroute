# GreenRoute backend

Routes each AI request to a **local model** (Ollama) when possible, and to the
**cloud** (Google Gemini, free tier) when not. **If there's no local model, it still works** —
requests go to the cloud and the response includes a `notice` saying so.

---

## Quick start (Windows)

**You need:** Python 3.10+ and a free Gemini API key: go to https://aistudio.google.com/apikey, sign in with Google, and click **Create API key**.

1. Open the `greenroute\backend` folder and **double-click `start.bat`**.
2. The first time, Notepad opens `.env`. Paste your key right after `GEMINI_API_KEY=`, then save and close it.
   Press any key in the terminal to continue.
3. The script checks your computer and asks what to do about the local model:
   - **Ollama not installed:** it asks whether to install it. Answer `n` to skip. The app then runs cloud-only, which is fine for a demo.
   - **Installed but not running:** it offers to start it.
   - **Model not downloaded:** it offers to download the recommended one (1–2 GB).
4. The server starts. Open **http://localhost:8000/docs** to try it in your browser:
   click `POST /chat` → *Try it out* → set `{"prompt": "hello"}` → *Execute*.

Press **Ctrl+C** in the terminal to stop the server. To start it again, just run `start.bat` again.

### Manual start (any OS)
```
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env            # macOS/Linux: cp  — then add your GEMINI_API_KEY
python setup_local.py             # optional local-model setup
uvicorn app:app --port 8000
```

---

## Ollama not opening or responding?

Run `python setup_local.py`. It detects the problem and tries to start Ollama for you. If that fails:

1. **Restart it:** right-click the llama icon in the system tray and choose **Quit**. Then open a terminal, run
   `ollama serve`, and leave that window open.
2. **Port conflict:** if you see "address already in use", run `netstat -ano | findstr 11434`
   and end that PID in Task Manager.
3. **Check the log:** `%LOCALAPPDATA%\Ollama\server.log`
4. **Reinstall:** run `winget install Ollama.Ollama`, or download it from https://ollama.com/download
5. **Test it:** open http://localhost:11434 in a browser. It should say *"Ollama is running"*.

**Or skip it.** With no local model, everything routes to the cloud automatically.
When Ollama comes back, the server picks it up within 10 seconds, with no restart needed.

---

## API

| Endpoint | What it does |
|---|---|
| `GET /health` | Local model status and the cloud model name |
| `GET /setup` | Device specs, recommended model, local status, and install steps (for a setup panel in the UI) |
| `POST /local/pull` | Start downloading a local model (`{"model": ...}`, defaults to the recommended one) |
| `GET /local/pull` | Download progress: `{state, status, pct, error}` |
| `POST /local/use` | Switch to a model that's already installed (`{"model": "mistral:latest"}`) |
| `POST /route` | Routing decision only (no inference) |
| `POST /chat` | Routes the request and returns the answer |

`POST /chat` body: `{"prompt": "...", "route": "auto" | "local" | "cloud"}`

Response:
```json
{
  "decision": "cloud",
  "model": "gemini-2.5-flash",
  "reason": "Default: local-first -> no local model available, routed to cloud",
  "notice": "No local model available: Ollama is not installed... Using cloud instead.",
  "simulated": false,
  "response": "...",
  "input_tokens": 12, "output_tokens": 40, "latency_ms": 900
}
```
`notice` is `null` when nothing went wrong. Show it as a banner in the UI when it's set.

## Settings (`.env`)
| Key | Default | Meaning |
|---|---|---|
| `LOCAL_MODEL` | `llama3.2:3b` | Ollama model (`setup_local.py` may switch this to fit your RAM) |
| `LOCAL_UNAVAILABLE` | `cloud` | `cloud` = fall back with a notice · `simulate` = small cloud model labelled local · `error` = return 503 |
| `GEMINI_API_KEY` | (empty) | Free key from https://aistudio.google.com/apikey |
| `CLOUD_MODEL` | `gemini-2.5-flash` | Cloud fallback model (e.g. `gemini-2.5-flash-lite` for speed, `gemini-2.5-pro` for quality) |

## Files
- `app.py`: API server
- `router.py`: routing decision (Phase 2 heuristics go in `decide()`)
- `system_check.py`: device specs and Ollama detection
- `setup_local.py`: interactive local-model setup
- `local_backend.py` / `cloud_backend.py`: Ollama and Gemini calls

## Gemini free-tier notes
- Rate limits are low (a few requests per minute on some models). A `429` means you should wait a minute. For the demo, `gemini-2.5-flash-lite` has the most headroom.
- On the free tier, Google may use your prompts to improve its products, so don't send sensitive data.
- If a model name stops working (`404`), set `CLOUD_MODEL` in `.env` to a current one from https://ai.google.dev/gemini-api/docs/models
