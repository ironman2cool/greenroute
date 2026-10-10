#!/usr/bin/env bash
# GreenRoute one-command start (macOS / Linux):  ./start.sh
set -e
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "[1/4] Creating Python environment..."
  python3 -m venv .venv
fi
echo "[2/4] Installing dependencies..."
.venv/bin/python -m pip install -q -r requirements.txt

[ -f .env ] || cp .env.example .env
if ! grep -q "^GEMINI_API_KEY=." .env; then
  echo
  echo "  No Gemini API key yet. Get a FREE one at https://aistudio.google.com/apikey"
  echo "  then paste it after GEMINI_API_KEY= in backend/.env and run this script again."
  exit 1
fi

echo "[3/4] Checking this device for local AI..."
.venv/bin/python setup_local.py

echo
echo "[4/4] Starting server at http://localhost:8000   (API docs: http://localhost:8000/docs)"
exec .venv/bin/python -m uvicorn app:app --port 8000
