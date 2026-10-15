"""Regression tests for bounded General Guide provider arbitration."""
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



def test_general_guide_tries_second_independent_fallback_after_fast_failures(monkeypatch):
    _isolate(monkeypatch)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def fast_failures_then_success(use_core, item, messages, max_tokens, schema, timeout_override=None):
        calls.append((item["provider"], timeout_override))
        if len(calls) < 3:
            clock.value += 0.25
            raise RuntimeError("simulated fast provider failure")
        return json.dumps({"response": "A grounded answer in three short paragraphs."})

    monkeypatch.setattr(provider_bank, "_call", fast_failures_then_success)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": "Return one JSON object."}],
        max_tokens=1200,
        parse=provider_bank._json_object,
        operation="general_guide_composition",
    )

    assert result is not None
    assert result["provider"] == "groq"
    assert [provider for provider, _ in calls] == ["gemini", "workers_ai", "groq"]
    assert all(timeout == provider_bank.GENERAL_GUIDE_PROVIDER_CALL_TIMEOUT_SECONDS for _, timeout in calls)
    assert provider_bank.GENERAL_GUIDE_FAST_FALLBACK_MAX_CANDIDATES == 2
    assert clock.value == 0.5

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
    assert provider_bank.GENERAL_GUIDE_PROVIDER_CALL_TIMEOUT_SECONDS == 2.0
    assert provider_bank.GENERAL_GUIDE_FAST_FAILURE_WINDOW_SECONDS == 5.0
