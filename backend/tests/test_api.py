"""API tests with both model backends replaced by fakes: no Ollama or Gemini needed."""
import json

import pytest
from fastapi.testclient import TestClient

import app as app_module
import cloud_backend
import config
import local_backend
import system_check
from conftest import NOT_INSTALLED, READY, SPECS


def fake_stream(text, model):
    def gen(prompt, m=None):
        for word in text.split(" "):
            yield {"type": "token", "text": word + " "}
        yield {"type": "usage", "model": m or model, "input_tokens": 7, "output_tokens": 3}
    return gen


def broken_stream(prompt, model=None):
    yield {"type": "token", "text": "partial "}
    raise local_backend.LocalUnavailable("Ollama crashed")


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(system_check, "ollama_status_cached", lambda ttl=10: READY)
    monkeypatch.setattr(system_check, "live_specs", lambda: SPECS)
    monkeypatch.setattr(local_backend, "generate", lambda p, m=None, max_tokens=None:
                        {"text": "Tokyo", "model": m, "input_tokens": 7, "output_tokens": 2})
    monkeypatch.setattr(cloud_backend, "generate", lambda p, m=None, **kw:
                        {"text": "A long essay", "model": m, "input_tokens": 9, "output_tokens": 900})
    monkeypatch.setattr(local_backend, "stream", fake_stream("Tokyo is the capital", "llama3.2:1b"))
    monkeypatch.setattr(cloud_backend, "stream", fake_stream("Cloud answer here", "gemini-2.5-flash"))
    with TestClient(app_module.app) as c:
        yield c


def events(client, body):
    with client.stream("POST", "/chat/stream", json=body) as r:
        assert r.status_code == 200
        return [json.loads(line) for line in r.iter_lines() if line]


def test_page_is_served(client):
    r = client.get("/")
    assert r.status_code == 200 and "GreenRoute" in r.text


def test_chat_local_records_savings(client):
    r = client.post("/chat", json={"prompt": "What's the capital of Japan?"}).json()
    assert r["decision"] == "local" and r["response"] == "Tokyo"
    assert r["impact"]["saved"]["water_ml"] == pytest.approx(0.26)
    assert r["stats"]["local"] == 1


def test_chat_cloud(client):
    r = client.post("/chat", json={"prompt": "Write a detailed 5-paragraph essay on energy policy."}).json()
    assert r["decision"] == "cloud" and r["output_tokens"] == 900
    assert r["impact"]["saved"]["wh"] == 0


def test_chat_validation(client):
    assert client.post("/chat", json={"prompt": "   "}).status_code == 400
    assert client.post("/chat", json={"prompt": "hi", "route": "moon"}).status_code == 422


def test_route_preview_has_details(client):
    r = client.post("/route", json={"prompt": "hi", "device": {"low_spec": True}}).json()
    assert r["decision"] == "cloud"
    assert r["details"]["classification"]["task"] == "chat"
    assert any(not c["ok"] and c["name"] == "Device mode" for c in r["details"]["checks"])


def test_stream_local(client):
    ev = events(client, {"prompt": "What's the capital of Japan?"})
    assert ev[0]["type"] == "decision" and ev[0]["decision"] == "local"
    assert "".join(e["text"] for e in ev if e["type"] == "token").strip() == "Tokyo is the capital"
    done = ev[-1]
    assert done["type"] == "done" and done["decision"] == "local" and done["output_tokens"] == 3
    assert done["stats"]["requests"] == 1


def test_stream_falls_back_to_cloud_when_local_breaks(client, monkeypatch):
    monkeypatch.setattr(local_backend, "stream", broken_stream)
    ev = events(client, {"prompt": "What's the capital of Japan?"})
    kinds = [e["type"] for e in ev]
    assert kinds[0] == "decision" and "fallback" in kinds and kinds[-1] == "done"
    fb = next(e for e in ev if e["type"] == "fallback")
    assert fb["reset"] is True and fb["decision"] == "cloud" and "Ollama crashed" in fb["notice"]
    assert ev[-1]["decision"] == "cloud"


def test_stream_error_mode(client, monkeypatch):
    monkeypatch.setattr(local_backend, "stream", broken_stream)
    monkeypatch.setattr(config, "LOCAL_UNAVAILABLE", "error")
    ev = events(client, {"prompt": "hi"})
    assert ev[-1]["type"] == "error"


def test_stream_cloud_error_is_reported(client, monkeypatch):
    def fail(prompt, m=None):
        raise cloud_backend.CloudError("Gemini 429: free-tier rate limit hit")
        yield  # pragma: no cover
    monkeypatch.setattr(cloud_backend, "stream", fail)
    ev = events(client, {"prompt": "Write a detailed essay on tax policy"})
    assert ev[-1] == {"type": "error", "detail": "Gemini 429: free-tier rate limit hit"}


def test_no_local_model_routes_to_cloud_with_notice(client, monkeypatch):
    monkeypatch.setattr(system_check, "ollama_status_cached", lambda ttl=10: NOT_INSTALLED)
    r = client.post("/chat", json={"prompt": "hi"}).json()
    assert r["decision"] == "cloud" and "No local model available" in r["notice"]


def test_image_request_gets_notice(client):
    r = client.post("/route", json={"prompt": "Generate an image of a cat"}).json()
    assert r["decision"] == "cloud" and "image" in r["notice"]


def test_cloud_model_fallback_note_reaches_the_client(client, monkeypatch):
    def with_note(prompt, m=None):
        yield {"type": "note", "text": "gemini-2.5-flash is out of free quota; trying the next cloud model."}
        yield from fake_stream("Fallback answer", "gemini-3.5-flash-lite")(prompt)
    monkeypatch.setattr(cloud_backend, "stream", with_note)
    ev = events(client, {"prompt": "Write a detailed essay on tax policy"})
    assert any(e["type"] == "note" and "out of free quota" in e["text"] for e in ev)
    assert ev[-1]["model"] == "gemini-3.5-flash-lite"


def test_image_prompts_ask_the_text_model_for_a_description(client, monkeypatch):
    seen = {}

    def capture(prompt, m=None, **kw):
        seen["prompt"] = prompt
        return {"text": "A cat in a yellow raincoat.", "model": m, "input_tokens": 1, "output_tokens": 1}
    monkeypatch.setattr(cloud_backend, "generate", capture)
    client.post("/chat", json={"prompt": "Generate an image of a cat"})
    assert "can't draw images" in seen["prompt"] and seen["prompt"].endswith("Generate an image of a cat")


def test_stats_endpoints(client):
    client.post("/chat", json={"prompt": "hi"})
    s = client.get("/stats").json()
    assert s["requests"] == 1 and s["sources"] and s["assumptions"]["device_active_watts"] > 0
    assert client.post("/stats/reset").json()["requests"] == 0
