"""Guard rail: fail the build if a secret is ever committed.

Each user supplies their own key in backend/.env, which .gitignore keeps out of the repo.
This test checks every tracked file, so a slip (committing .env, or pasting a key into code
or docs) breaks CI before it reaches anyone who downloads the project.
"""
import os
import re
import shutil
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KEY_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),          # Google API keys
    re.compile(r"\bAQ\.[0-9A-Za-z_-]{30,}"),         # Google AI Studio keys
    re.compile(r"sk-(ant-|proj-)?[0-9A-Za-z_-]{30,}"),  # Anthropic / OpenAI keys
]


def tracked_files():
    if not shutil.which("git") or not os.path.isdir(os.path.join(ROOT, ".git")):
        pytest.skip("not a git checkout")
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [f for f in out.splitlines() if f]


def test_no_env_file_is_tracked():
    assert not [f for f in tracked_files() if os.path.basename(f) == ".env"]


def test_no_api_keys_in_tracked_files():
    leaks = []
    for f in tracked_files():
        path = os.path.join(ROOT, f)
        if not os.path.isfile(path) or f.endswith((".png", ".jpg", ".ico")):
            continue
        with open(path, encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
        leaks += [f"{f}: {m.group(0)[:8]}..." for p in KEY_PATTERNS for m in p.finditer(text)]
    assert not leaks, f"Possible API keys committed: {leaks}"


def test_env_template_has_no_key():
    with open(os.path.join(ROOT, "backend", ".env.example"), encoding="utf-8") as fh:
        line = next(l for l in fh if l.startswith("GEMINI_API_KEY="))
    assert line.strip() == "GEMINI_API_KEY="
