"""Cloud fallback via the Google Gemini API (free tier key from AI Studio).

The free tier gives each model its own small daily quota (20 requests/day for gemini-2.5-flash
in Oct 2026). So when the primary model is out of quota, overloaded or retired, a request moves
down config.CLOUD_FALLBACK_MODELS instead of failing, and the answer says which model replied.
"""
from typing import Iterator

import httpx
from google import genai
from google.genai import errors, types

import config

_client = None
_FALLBACK_CODES = {404, 429, 500, 503}  # retired, out of quota, internal error, overloaded


class CloudError(Exception):
    pass


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not config.GEMINI_API_KEY:
            raise CloudError("No Gemini API key - set GEMINI_API_KEY in .env "
                             "(free key: https://aistudio.google.com/apikey)")
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client


def _is_gemma(model: str) -> bool:
    return model.startswith("gemma")


def _contents(model: str, prompt: str, system: str | None) -> str:
    # Gemma models on the Gemini API reject system instructions, so the instruction goes inline.
    return f"{system or config.SYSTEM_PROMPT}\n\n{prompt}" if _is_gemma(model) else prompt


def _config(model: str, system: str | None = None, **extra) -> types.GenerateContentConfig:
    cfg = types.GenerateContentConfig(
        max_output_tokens=config.CLOUD_MAX_TOKENS,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        **extra,
    )
    if not _is_gemma(model):
        cfg.system_instruction = system or config.SYSTEM_PROMPT
    if model.startswith("gemini-2.5-flash"):  # thinking off = faster replies
        cfg.thinking_config = types.ThinkingConfig(thinking_budget=0)
    return cfg


def _chain(model: str, fallback: bool) -> list[str]:
    return [model] + ([m for m in config.CLOUD_FALLBACK_MODELS if m != model] if fallback else [])


def _error(e: Exception, model: str) -> CloudError:
    """Turn any SDK/network failure into a CloudError a person can act on."""
    if isinstance(e, errors.ClientError):
        hints = {
            400: f"bad request - {e.message} (check GEMINI_API_KEY and CLOUD_MODEL)",
            403: "API key rejected - check GEMINI_API_KEY",
            404: f"model '{model}' not found - set CLOUD_MODEL in .env",
            429: "free-tier quota used up for every configured model - try again later",
        }
        return CloudError(f"Gemini {e.code}: {hints.get(e.code, e.message)}")
    if isinstance(e, errors.APIError):
        return CloudError(f"Gemini server error {e.code}: {e.message}")
    return CloudError("Could not reach the Gemini API - check your internet connection")


_ERRORS = (errors.APIError, httpx.HTTPError, OSError)


def _can_fall_back(e: Exception) -> bool:
    return isinstance(e, errors.APIError) and e.code in _FALLBACK_CODES


def _why(e: errors.APIError) -> str:
    return {404: "isn't available", 429: "is out of free quota", 503: "is overloaded"}.get(e.code, "failed")


def _usage(meta) -> tuple[int, int]:
    return ((meta and meta.prompt_token_count) or 0, (meta and meta.candidates_token_count) or 0)


def generate(prompt: str, model: str | None = None, system: str | None = None,
             fallback: bool = True, **extra) -> dict:
    notes, last = [], None
    for m in _chain(model or config.CLOUD_MODEL, fallback):
        try:
            resp = _get_client().models.generate_content(model=m, contents=_contents(m, prompt, system),
                                                         config=_config(m, system, **extra))
        except _ERRORS as e:
            if not _can_fall_back(e):
                raise _error(e, m) from e
            last = e
            notes.append(f"{m} {_why(e)}")
            continue
        inp, out = _usage(resp.usage_metadata)
        return {
            "text": resp.text or "[Gemini returned no text - the request may have been blocked.]",
            "model": m,
            "input_tokens": inp,
            "output_tokens": out,
            "note": "; ".join(notes) + f" - answered by {m}" if notes else None,
        }
    raise _error(last, model or config.CLOUD_MODEL) from last


def stream(prompt: str, model: str | None = None, fallback: bool = True) -> Iterator[dict]:
    """Same event shape as local_backend.stream(), plus {"type": "note"} when a fallback model is used."""
    last = None
    for m in _chain(model or config.CLOUD_MODEL, fallback):
        meta, any_text = None, False
        try:
            for chunk in _get_client().models.generate_content_stream(
                    model=m, contents=_contents(m, prompt, None), config=_config(m)):
                if chunk.text:
                    any_text = True
                    yield {"type": "token", "text": chunk.text}
                meta = chunk.usage_metadata or meta
        except _ERRORS as e:
            if any_text or not _can_fall_back(e):  # can't switch models half-way through an answer
                raise _error(e, m) from e
            last = e
            yield {"type": "note", "text": f"{m} {_why(e)}; trying the next cloud model."}
            continue
        if not any_text:
            yield {"type": "token", "text": "[Gemini returned no text - the request may have been blocked.]"}
        inp, out = _usage(meta)
        yield {"type": "usage", "model": m, "input_tokens": inp, "output_tokens": out}
        return
    raise _error(last, model or config.CLOUD_MODEL) from last
