"""Bounded independent-provider fallback for HRN's perception stage."""
import json
import provider_bank


def _candidate(provider, model):
    return {
        "provider": provider,
        "model": model,
        "health_state": "healthy",
        "quality_failures": 0,
        "transport_failures": 0,
        "consecutive_failures": 0,
        "last_success": 100.0,
        "capabilities": ["json_object", "relational_analysis"],
    }


def _isolate(monkeypatch, candidates):
    monkeypatch.setattr(provider_bank, "select", lambda *args, **kwargs: candidates)
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    monkeypatch.setattr(provider_bank, "_blocked", lambda state: False)
    monkeypatch.setattr(provider_bank, "acquire_probe", lambda state: True)
    monkeypatch.setattr(provider_bank, "_failure", lambda *args, **kwargs: None)
    monkeypatch.setattr(provider_bank, "_success", lambda *args, **kwargs: None)
    monkeypatch.setattr(provider_bank, "_state", lambda provider, model: provider_bank.new_state(provider, model))


def test_perception_fast_failures_can_reach_fifth_independent_provider(monkeypatch):
    candidates = [
        _candidate("gemini", "model-a"),
        _candidate("mistral", "model-b"),
        _candidate("workers_ai", "model-c"),
        _candidate("nvidia", "model-d"),
        _candidate("groq", "model-e"),
    ]
    _isolate(monkeypatch, candidates)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def fake_call(use_core, item, messages, max_tokens, schema=None, timeout_override=None):
        calls.append((item["provider"], timeout_override))
        if item["provider"] != "groq":
            clock.value += 0.20
            raise provider_bank.ProviderCallError(
                "simulated fast provider failure",
                item["provider"],
                item["model"],
                429 if item["provider"] == "mistral" else 503,
                category="rate_limited" if item["provider"] == "mistral" else "http_error",
            )
        return json.dumps({"perception": "bounded synthetic result"})

    monkeypatch.setattr(provider_bank, "_quota_guarded_call", fake_call)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "user", "content": "synthetic calibration input"}],
        max_tokens=100,
        parse=provider_bank._json_object,
        operation="hrn_perception",
    )

    assert result is not None
    assert result["provider"] == "groq"
    assert [provider for provider, _ in calls] == ["gemini", "mistral", "workers_ai", "nvidia", "groq"]
    assert all(timeout == provider_bank.HRN_PROVIDER_CALL_TIMEOUT_SECONDS for _, timeout in calls)
    assert provider_bank.HRN_PERCEPTION_FAST_FALLBACK_MAX_CANDIDATES == 4
    assert provider_bank.HRN_PERCEPTION_FAST_FAILURE_WINDOW_SECONDS == 3.0


def test_perception_does_not_spend_turn_budget_on_fallback_after_slow_failure(monkeypatch):
    candidates = [_candidate("groq", "model-a"), _candidate("nvidia", "model-b")]
    _isolate(monkeypatch, candidates)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def slow_failure(use_core, item, messages, max_tokens, schema=None, timeout_override=None):
        calls.append(item["provider"])
        clock.value += 3.5
        raise RuntimeError("simulated slow timeout")

    monkeypatch.setattr(provider_bank, "_quota_guarded_call", slow_failure)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "user", "content": "synthetic calibration input"}],
        max_tokens=100,
        parse=provider_bank._json_object,
        operation="hrn_perception",
    )

    assert result is None
    assert calls == ["groq"]



def test_empty_movement_brief_is_input_failure_not_provider_quality_failure():
    reason = "hrn_relational question-surface contract violation: question-grounding contract violation: movement brief has no concrete question anchors"
    assert provider_bank._is_movement_brief_input_failure("hrn_relational", reason)
    assert not provider_bank._is_movement_brief_input_failure(
        "hrn_relational",
        "question-grounding contract violation: question does not name a concrete detail from the movement brief",
    )
    assert not provider_bank._is_movement_brief_input_failure(
        "general_guide_composition",
        reason,
    )
