"""Regression tests for bounded General Guide provider arbitration."""
import pytest
import json

import provider_bank


def _item(provider, model):
    return {
        "provider": provider,
        "model": model,
        "health_state": "healthy",
        "quality_failures": 0,
        "transport_failures": 0,
        "consecutive_failures": 0,
        "last_success": 100.0,
        "capabilities": ["json_object", "long_context", "composition"],
    }


def _isolate(monkeypatch):
    candidates = [
        _item("gemini", "gemini-3.8-flash"),
        _item("workers_ai", "@cf/google/gemma-4-26b-a4b-it"),
        _item("groq", "openai/gpt-oss-20b"),
        _item("mistral", "mistral-small-latest"),
    ]
    monkeypatch.setattr(provider_bank, "select", lambda *args, **kwargs: candidates)
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    monkeypatch.setattr(provider_bank, "_blocked", lambda state, operation=None: False)
    monkeypatch.setattr(provider_bank, "acquire_probe", lambda state: True)
    monkeypatch.setattr(provider_bank, "_failure", lambda *args, **kwargs: None)
    monkeypatch.setattr(provider_bank, "_success", lambda *args, **kwargs: None)
    monkeypatch.setattr(provider_bank, "_record_quality_rejection", lambda *args, **kwargs: None)
    states = {}

    def fake_state(provider, model):
        key = provider + ":" + model
        if key not in states:
            states[key] = provider_bank.new_state(provider, model)
        return states[key]

    monkeypatch.setattr(provider_bank, "_state", fake_state)
    monkeypatch.setattr(provider_bank, "_normalize_operation_result", lambda operation, parsed, messages=None: parsed)


def test_general_guide_uses_bounded_timeout_and_one_independent_fallback(monkeypatch):
    _isolate(monkeypatch)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def fake_call(use_core, item, messages, max_tokens, schema, timeout_override=None):
        calls.append((item["provider"], timeout_override))
        if len(calls) == 1:
            clock.value += 1.0
            raise RuntimeError("simulated fast provider failure")
        return json.dumps({"response": "A grounded answer in three short paragraphs."})

    monkeypatch.setattr(provider_bank, "_call", fake_call)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": "Return one JSON object."}],
        max_tokens=1200,
        parse=provider_bank._json_object,
        operation="general_guide_composition",
    )

    assert result is not None
    assert result["provider"] == "workers_ai"
    assert calls == [
        ("gemini", provider_bank.GENERAL_GUIDE_PROVIDER_CALL_TIMEOUT_SECONDS),
        ("workers_ai", provider_bank.GENERAL_GUIDE_PROVIDER_CALL_TIMEOUT_SECONDS),
    ]



def test_general_guide_stops_after_one_failed_fallback(monkeypatch):
    _isolate(monkeypatch)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def fast_failures_then_success(use_core, item, messages, max_tokens, schema, timeout_override=None):
        calls.append((item["provider"], timeout_override))
        clock.value += 0.25
        raise RuntimeError("simulated fast provider failure")

    monkeypatch.setattr(provider_bank, "_call", fast_failures_then_success)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": "Return one JSON object."}],
        max_tokens=1200,
        parse=provider_bank._json_object,
        operation="general_guide_composition",
    )

    assert result is None
    assert [provider for provider, _ in calls] == ["gemini", "workers_ai"]
    assert all(timeout == provider_bank.GENERAL_GUIDE_PROVIDER_CALL_TIMEOUT_SECONDS for _, timeout in calls)
    assert provider_bank.GENERAL_GUIDE_FAST_FALLBACK_MAX_CANDIDATES == 1
    assert clock.value == 0.5


def test_general_guide_prioritizes_healthy_lane_over_half_open_probe(monkeypatch):
    candidates = [
        {**_item("workers_ai", "@cf/google/gemma-4-26b-a4b-it"), "health_state": "half_open", "last_success": 90.0},
        {**_item("nvidia", "nvidia/nemotron-3.5-lightning-30b-a3b"), "health_state": "healthy", "last_success": 80.0},
        {**_item("groq", "openai/gpt-oss-20b"), "health_state": "half_open", "last_success": 70.0},
    ]
    monkeypatch.setattr(provider_bank, "candidates", lambda *args, **kwargs: candidates)
    monkeypatch.setattr(provider_bank, "_csv", lambda _name: [])
    monkeypatch.setitem(provider_bank._STATE, "provider_cursor", 0)
    monkeypatch.setitem(provider_bank._STATE, "model_cursors", {})

    selected = provider_bank.select(use_core=None, operation="general_guide_composition")

    assert selected
    assert selected[0]["provider"] == "nvidia"
    assert selected[0]["health_state"] == "healthy"



def test_general_guide_interleaves_independent_provider_lanes(monkeypatch):
    candidates = [
        _item("workers_ai", "@cf/google/gemma-4-26b-a4b-it"),
        _item("workers_ai", "@cf/meta/llama-3.3-70b-instruct-fp8-fast"),
        _item("nvidia", "nvidia/nemotron-3.5-lightning-30b-a3b"),
        _item("groq", "openai/gpt-oss-20b"),
    ]
    monkeypatch.setattr(provider_bank, "candidates", lambda *args, **kwargs: candidates)
    monkeypatch.setattr(provider_bank, "_csv", lambda _name: ["workers_ai", "nvidia", "groq"])
    monkeypatch.setitem(provider_bank._STATE, "provider_cursor", 0)
    monkeypatch.setitem(provider_bank._STATE, "model_cursors", {})

    selected = provider_bank.select(use_core=None, operation="general_guide_composition")
    providers = [item["provider"] for item in selected]

    assert len(providers) == 4
    assert len(set(providers[:3])) == 3
    assert providers[3] == "workers_ai"

def test_general_guide_does_not_walk_to_fourth_candidate(monkeypatch):
    _isolate(monkeypatch)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def failures_then_success(use_core, item, messages, max_tokens, schema, timeout_override=None):
        calls.append((item["provider"], timeout_override))
        clock.value += 0.2
        raise RuntimeError("simulated fast provider failure")

    monkeypatch.setattr(provider_bank, "_call", failures_then_success)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": "Return one JSON object."}],
        max_tokens=1200,
        parse=provider_bank._json_object,
        operation="general_guide_composition",
    )

    assert result is None
    assert [provider for provider, _ in calls] == ["gemini", "workers_ai"]
    assert all(timeout == provider_bank.GENERAL_GUIDE_PROVIDER_CALL_TIMEOUT_SECONDS for _, timeout in calls)
    assert clock.value == pytest.approx(0.4)

def test_general_guide_does_not_chain_after_slow_first_failure(monkeypatch):
    _isolate(monkeypatch)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def slow_failure(use_core, item, messages, max_tokens, schema, timeout_override=None):
        calls.append((item["provider"], timeout_override))
        clock.value += 6.0
        raise RuntimeError("simulated slow provider failure")

    monkeypatch.setattr(provider_bank, "_call", slow_failure)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": "Return one JSON object."}],
        max_tokens=1200,
        parse=provider_bank._json_object,
        operation="general_guide_composition",
    )

    assert result is None
    assert calls == [("gemini", provider_bank.GENERAL_GUIDE_PROVIDER_CALL_TIMEOUT_SECONDS)]
    assert provider_bank.GENERAL_GUIDE_PROVIDER_CALL_TIMEOUT_SECONDS == 1.25
    assert provider_bank.GENERAL_GUIDE_FAST_FAILURE_WINDOW_SECONDS == 2.8
