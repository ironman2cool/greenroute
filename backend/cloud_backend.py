"""Cloud fallback via the Google Gemini API (free tier key from AI Studio)."""
from google import genai
from google.genai import errors, types

import config

_client = None


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


def generate(prompt: str, model: str | None = None) -> dict:
    model = model or config.CLOUD_MODEL
    cfg = types.GenerateContentConfig(
        system_instruction=config.SYSTEM_PROMPT,
        max_output_tokens=config.CLOUD_MAX_TOKENS,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    if "flash" in model:  # thinking off = faster demo replies (flash models only)
        cfg.thinking_config = types.ThinkingConfig(thinking_budget=0)

    try:
        resp = _get_client().models.generate_content(model=model, contents=prompt, config=cfg)
    except errors.ClientError as e:
        hints = {
            400: f"bad request - {e.message} (check GEMINI_API_KEY and CLOUD_MODEL)",
            403: "API key rejected - check GEMINI_API_KEY",
            404: f"model '{model}' not found - set CLOUD_MODEL in .env",
            429: "free-tier rate limit hit - wait a minute and retry",
        }
        raise CloudError(f"Gemini {e.code}: {hints.get(e.code, e.message)}") from e
    except errors.APIError as e:
        raise CloudError(f"Gemini server error {e.code}: {e.message}") from e
    except OSError as e:
        raise CloudError("Could not reach the Gemini API - check your internet connection") from e

    usage = resp.usage_metadata
    return {
        "text": resp.text or "[Gemini returned no text - the request may have been blocked.]",
        "model": model,
        "input_tokens": (usage and usage.prompt_token_count) or 0,
        "output_tokens": (usage and usage.candidates_token_count) or 0,
    }
