import config
import router
from conftest import NOT_INSTALLED, READY, SPECS


def decide(prompt, **kw):
    kw.setdefault("local_status", READY)
    kw.setdefault("specs", SPECS)
    return router.decide(prompt, **kw)


def test_simple_question_runs_locally_with_reason():
    d = decide("What's the capital of Japan?")
    assert d.decision == "local" and d.model == "llama3.2:1b"
    assert "on-device" in d.reason
    assert all(c["ok"] for c in d.details["checks"])


def test_complex_request_goes_to_cloud_and_names_the_limit():
    d = decide("Write a detailed 5-paragraph essay on renewable energy policy.")
    assert d.decision == "cloud" and d.model == config.CLOUD_MODEL
    assert "Long-form writing" in d.reason and "limit 0.35" in d.reason


def test_bigger_local_model_gets_a_higher_limit():
    prompt = "Write a python function that parses a CSV file and returns the average of each numeric column"
    small = decide(prompt)
    big = decide(prompt, local_status={**READY, "model_params_b": 8.0, "model_size_gb": 4.9})
    assert small.decision == "cloud" and big.decision == "local"


def test_image_requests_go_to_cloud():
    assert decide("Generate an image of a cat").decision == "cloud"


def test_low_spec_toggle_flips_a_simple_prompt_to_cloud():
    d = decide("What's the capital of Japan?", device={"low_spec": True})
    assert d.decision == "cloud" and "Low-spec" in d.reason


def test_low_battery_only_matters_when_unplugged():
    low_unplugged = decide("hi", device={"battery_pct": 12, "on_battery": True})
    low_plugged = decide("hi", device={"battery_pct": 12, "on_battery": False})
    assert low_unplugged.decision == "cloud" and "Battery at 12%" in low_unplugged.reason
    assert low_plugged.decision == "local"


def test_server_side_battery_reading_is_used_without_client_hints():
    d = decide("hi", specs={"ram_free_gb": 6, "battery_pct": 9, "on_battery": True})
    assert d.decision == "cloud"


def test_long_input_goes_to_cloud():
    d = decide("Summarize: " + "lorem ipsum " * 1000)
    assert d.decision == "cloud" and "too long" in d.reason


def test_unclassified_prompt_goes_to_cloud_to_be_safe():
    d = decide("Bananas")
    assert d.decision == "cloud" and "classify" in d.reason


def test_low_memory_blocks_loading_but_not_an_already_loaded_model():
    not_loaded = {**READY, "loaded": False}
    assert decide("hi", local_status=not_loaded, specs={"ram_free_gb": 0.5}).decision == "cloud"
    assert decide("hi", local_status=READY, specs={"ram_free_gb": 0.5}).decision == "local"


def test_forced_routes():
    assert decide("Write a 2000-word essay", force="local").decision == "local"
    assert decide("hi", force="cloud").decision == "cloud"


def test_missing_local_model_falls_back_with_notice():
    d = decide("hi", local_status=NOT_INSTALLED)
    assert d.decision == "cloud"
    assert d.notice and "No local model available" in d.notice


def test_cloud_decisions_never_show_the_missing_model_notice():
    d = decide("Write a detailed essay on tax policy", local_status=NOT_INSTALLED)
    assert d.decision == "cloud" and d.notice is None


def test_simulate_mode_keeps_local_decision(monkeypatch):
    monkeypatch.setattr(config, "LOCAL_UNAVAILABLE", "simulate")
    assert decide("hi", local_status=NOT_INSTALLED).decision == "local"


def test_model_capability_tiers():
    assert router.model_capability(None) == 0.35
    assert router.model_capability(1.2) == 0.35
    assert router.model_capability(3.2) == 0.5
    assert router.model_capability(7.2) == 0.6
    assert router.model_capability(70) == 0.7
