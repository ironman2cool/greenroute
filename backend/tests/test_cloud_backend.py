"""Cloud fallback chain, tested against a fake Gemini client (no network)."""
from types import SimpleNamespace

import pytest
from google.genai import errors

import cloud_backend
import config


def api_error(code):
    cls = errors.ClientError if code < 500 else errors.ServerError
    return cls(code, {"error": {"code": code, "message": f"err {code}", "status": "X"}})


class FakeModels:
    def __init__(self, failures):
        self.failures, self.calls = failures, []

    def generate_content(self, model, contents, config):
        self.calls.append((model, contents, config))
        if model in self.failures:
            raise api_error(self.failures[model])
        usage = SimpleNamespace(prompt_token_count=5, candidates_token_count=2)
        return SimpleNamespace(text=f"answer from {model}", usage_metadata=usage)

    def generate_content_stream(self, model, contents, config):
        self.calls.append((model, contents, config))
        if model in self.failures:
            raise api_error(self.failures[model])
        usage = SimpleNamespace(prompt_token_count=5, candidates_token_count=2)
        yield SimpleNamespace(text="hello ", usage_metadata=None)
        yield SimpleNamespace(text=model, usage_metadata=usage)


@pytest.fixture
def fake(monkeypatch):
    monkeypatch.setattr(config, "CLOUD_MODEL", "gemini-2.5-flash")
    monkeypatch.setattr(config, "CLOUD_FALLBACK_MODELS", ["gemini-3.5-flash-lite", "gemma-4-26b-a4b-it"])

    def install(failures):
        models = FakeModels(failures)
        monkeypatch.setattr(cloud_backend, "_client", SimpleNamespace(models=models))
        return models
    return install


def test_primary_model_answers(fake):
    fake({})
    r = cloud_backend.generate("hi")
    assert r["model"] == "gemini-2.5-flash" and r["note"] is None


def test_quota_exhaustion_falls_back_and_says_so(fake):
    models = fake({"gemini-2.5-flash": 429, "gemini-3.5-flash-lite": 503})
    r = cloud_backend.generate("hi")
    assert r["model"] == "gemma-4-26b-a4b-it"
    assert "out of free quota" in r["note"] and "overloaded" in r["note"]
    assert [c[0] for c in models.calls] == ["gemini-2.5-flash", "gemini-3.5-flash-lite", "gemma-4-26b-a4b-it"]


def test_all_models_exhausted_raises_readable_error(fake):
    fake({m: 429 for m in ["gemini-2.5-flash", "gemini-3.5-flash-lite", "gemma-4-26b-a4b-it"]})
    with pytest.raises(cloud_backend.CloudError, match="quota"):
        cloud_backend.generate("hi")


def test_bad_key_does_not_fall_back(fake):
    models = fake({"gemini-2.5-flash": 403})
    with pytest.raises(cloud_backend.CloudError, match="API key rejected"):
        cloud_backend.generate("hi")
    assert len(models.calls) == 1


def test_fallback_can_be_disabled(fake):
    fake({"gemini-2.5-flash": 429})
    with pytest.raises(cloud_backend.CloudError):
        cloud_backend.generate("hi", fallback=False)


def test_gemma_gets_the_system_prompt_inline(fake):
    models = fake({})
    cloud_backend.generate("What is 2+2?", model="gemma-4-26b-a4b-it", system="Be terse.")
    _, contents, cfg = models.calls[0]
    assert contents.startswith("Be terse.") and "What is 2+2?" in contents
    assert cfg.system_instruction is None and cfg.thinking_config is None


def test_gemini_flash_gets_thinking_off_and_a_system_instruction(fake):
    models = fake({})
    cloud_backend.generate("hi")
    _, contents, cfg = models.calls[0]
    assert contents == "hi" and cfg.system_instruction and cfg.thinking_config.thinking_budget == 0


def test_stream_falls_back_with_a_note(fake):
    fake({"gemini-2.5-flash": 429})
    events = list(cloud_backend.stream("hi"))
    assert events[0]["type"] == "note" and "out of free quota" in events[0]["text"]
    assert "".join(e["text"] for e in events if e["type"] == "token") == "hello gemini-3.5-flash-lite"
    assert events[-1] == {"type": "usage", "model": "gemini-3.5-flash-lite", "input_tokens": 5, "output_tokens": 2}
