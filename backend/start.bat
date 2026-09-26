@echo off
REM GreenRoute one-click start (Windows). Double-click or run from a terminal.
cd /d "%~dp0"

if not exist .venv (
    echo [1/4] Creating Python environment...
    python -m venv .venv || (echo Python not found. Install Python 3.10+ from python.org & pause & exit /b 1)
)
echo [2/4] Installing dependencies...
.venv\Scripts\python -m pip install -q -r requirements.txt

if not exist .env copy .env.example .env >nul
findstr /r "^GEMINI_API_KEY=." .env >nul || (
    echo.
    echo  No Gemini API key yet. Get a FREE one at https://aistudio.google.com/apikey
    echo  ^(sign in with Google, click "Create API key", copy it^).
    echo  Notepad will open .env - paste the key right after GEMINI_API_KEY=  then save and close.
    start https://aistudio.google.com/apikey
    notepad .env
    pause
)

echo [3/4] Checking this device for local AI...
.venv\Scripts\python setup_local.py

echo.
echo [4/4] Starting server at http://localhost:8000   (API docs: http://localhost:8000/docs)
echo       Press Ctrl+C to stop.
.venv\Scripts\python -m uvicorn app:app --port 8000
