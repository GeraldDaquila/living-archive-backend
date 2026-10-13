"""Regression tests for state-aware Emergency Intelligence service selection."""

import safety_intelligence


def test_nonacute_safety_states_request_crisis_support(monkeypatch):
    calls = []

    def fake_request(**kwargs):
        calls.append(kwargs)
        return {}

    monkeypatch.setattr(safety_intelligence, "_request_emergency_intelligence", fake_request)
    monkeypatch.setattr(
        safety_intelligence,
        "_initial_deterministic_safety_response",
        lambda **kwargs: {"service_need": calls[-1]["service_need"]},
    )
    result = safety_intelligence.resolve_safety(
        query="I am having a hard time and need support.",
        safety_state="current",
        country="PH",
        location={"explicit_country": "PH"},
    )
    assert result["service_need"] == "crisis_support"


def test_acute_safety_states_request_general_emergency(monkeypatch):
    calls = []

    def fake_request(**kwargs):
        calls.append(kwargs)
        return {}

    monkeypatch.setattr(safety_intelligence, "_request_emergency_intelligence", fake_request)
    monkeypatch.setattr(
        safety_intelligence,
        "_initial_deterministic_safety_response",
        lambda **kwargs: {"service_need": calls[-1]["service_need"]},
    )
    result = safety_intelligence.resolve_safety(
        query="I may act on these thoughts right now.",
        safety_state="acute",
        country="PH",
        location={"explicit_country": "PH"},
    )
    assert result["service_need"] == "general_emergency"


def test_explicit_service_need_overrides_state_default(monkeypatch):
    calls = []

    def fake_request(**kwargs):
        calls.append(kwargs)
        return {}

    monkeypatch.setattr(safety_intelligence, "_request_emergency_intelligence", fake_request)
    monkeypatch.setattr(
        safety_intelligence,
        "_initial_deterministic_safety_response",
        lambda **kwargs: {"service_need": calls[-1]["service_need"]},
    )
    result = safety_intelligence.resolve_safety(
        query="A safety calibration test.",
        safety_state="acute",
        service_need="crisis_support",
        country="PH",
        location={"explicit_country": "PH"},
    )
    assert result["service_need"] == "crisis_support"
