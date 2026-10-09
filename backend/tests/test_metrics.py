import pytest

import config
import metrics


def test_cloud_request_saves_nothing():
    m = metrics.estimate("cloud", 3.0)
    assert m["actual"] == m["baseline"]
    assert m["saved"] == {"wh": 0, "gco2e": 0, "water_ml": 0}


def test_local_request_uses_power_times_time(monkeypatch):
    monkeypatch.setattr(config, "DEVICE_ACTIVE_WATTS", 36)
    monkeypatch.setattr(config, "GRID_GCO2_PER_KWH", 500)
    m = metrics.estimate("local", 10)  # 36 W x 10 s = 0.1 Wh
    assert m["actual"]["wh"] == pytest.approx(0.1)
    assert m["actual"]["gco2e"] == pytest.approx(0.05)
    assert m["actual"]["water_ml"] == 0
    assert m["saved"]["wh"] == pytest.approx(0.24 - 0.1)
    assert m["saved"]["water_ml"] == pytest.approx(0.26)


def test_slow_local_answer_can_cost_more_than_cloud(monkeypatch):
    monkeypatch.setattr(config, "DEVICE_ACTIVE_WATTS", 150)
    assert metrics.estimate("local", 30)["saved"]["wh"] < 0


def test_totals_persist_and_reset():
    assert metrics.stats()["requests"] == 0
    metrics.record("local", metrics.estimate("local", 2), 10, 20)
    metrics.record("cloud", metrics.estimate("cloud", 2), 10, 200)
    s = metrics.stats()
    assert (s["requests"], s["local"], s["cloud"]) == (2, 1, 1)
    assert s["output_tokens"] == 220
    assert s["local_share"] == 0.5
    assert s["saved"]["wh"] > 0 and s["saved"]["water_ml"] == pytest.approx(0.26)
    assert metrics.reset()["requests"] == 0
