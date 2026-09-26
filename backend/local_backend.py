"""Local inference via Ollama's HTTP API."""
import httpx

import config


class LocalUnavailable(Exception):
    pass


def generate(prompt: str, model: str | None = None) -> dict:
    model = model or config.LOCAL_MODEL
    try:
        r = httpx.post(
            f"{config.OLLAMA_URL}/api/chat",
            json={
                "model": model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": config.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=config.LOCAL_TIMEOUT_S,
        )
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
