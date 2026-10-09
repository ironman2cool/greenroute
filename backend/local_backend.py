"""Local inference via Ollama's HTTP API."""
import json
from typing import Iterator

import httpx

import config


class LocalUnavailable(Exception):
    pass


def _body(prompt: str, model: str, stream: bool, max_tokens: int | None) -> dict:
    body = {
        "model": model,
        "stream": stream,
        "messages": [
            {"role": "system", "content": config.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }
    if max_tokens:
        body["options"] = {"num_predict": max_tokens}
    return body


def generate(prompt: str, model: str | None = None, max_tokens: int | None = None) -> dict:
    model = model or config.LOCAL_MODEL
    try:
        r = httpx.post(f"{config.OLLAMA_URL}/api/chat", json=_body(prompt, model, False, max_tokens),
                       timeout=config.LOCAL_TIMEOUT_S)
    except httpx.HTTPError as e:
        raise LocalUnavailable(f"Ollama unreachable at {config.OLLAMA_URL}.") from e
    if r.status_code != 200:
        raise LocalUnavailable(f"Ollama error {r.status_code}: {r.text[:200]}")

    data = r.json()
    return {
        "text": data["message"]["content"],
        "model": model,
        "input_tokens": data.get("prompt_eval_count", 0),
        "output_tokens": data.get("eval_count", 0),
    }


def stream(prompt: str, model: str | None = None) -> Iterator[dict]:
    """Yields {"type": "token", "text": ...} events, then one {"type": "usage", ...} event.
    Raises LocalUnavailable if Ollama can't be reached or fails part-way."""
    model = model or config.LOCAL_MODEL
    try:
        with httpx.stream("POST", f"{config.OLLAMA_URL}/api/chat", json=_body(prompt, model, True, None),
                          timeout=config.LOCAL_TIMEOUT_S) as r:
            if r.status_code != 200:
                r.read()
                raise LocalUnavailable(f"Ollama error {r.status_code}: {r.text[:200]}")
            for line in r.iter_lines():
                if not line:
                    continue
                msg = json.loads(line)
                if "error" in msg:
                    raise LocalUnavailable(f"Ollama error: {msg['error']}")
                if text := msg.get("message", {}).get("content"):
                    yield {"type": "token", "text": text}
                if msg.get("done"):
                    yield {"type": "usage", "model": model,
                           "input_tokens": msg.get("prompt_eval_count", 0),
                           "output_tokens": msg.get("eval_count", 0)}
    except httpx.HTTPError as e:
        raise LocalUnavailable(f"Ollama unreachable at {config.OLLAMA_URL}.") from e
