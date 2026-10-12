"""Regression tests for HRN provider-budget alignment.

These tests are deterministic and never call an external provider.
"""
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
        "capabilities": [
            "json_object",
            "long_context",
            "composition",
            "relational_analysis",
        ],
    }


def _isolate_route(monkeypatch, candidates):
    monkeypatch.setenv("USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS", "1")
    monkeypatch.setattr(provider_bank, "select", lambda *args, **kwargs: candidates)
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    monkeypatch.setattr(provider_bank, "_blocked", lambda state: False)
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


def test_hrn_slow_provider_failure_yields_to_wordpress_mirror_budget(monkeypatch):
    candidates = [
        _item("groq", "openai/gpt-oss-120b"),
        _item("workers_ai", "@cf/google/gemma-4-26b-a4b-it"),
    ]
    _isolate_route(monkeypatch, candidates)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def slow_failure(use_core, item, messages, max_tokens, schema, timeout_override=None):
        calls.append((item["provider"], timeout_override))
        clock.value += 6.0
        raise RuntimeError("simulated slow provider timeout beyond the fast-failure window")

    monkeypatch.setattr(provider_bank, "_call", slow_failure)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": (
            "STRUCTURED MOVEMENT BRIEF\n"
            '{"working_hypothesis":"deadline disagreement",'
            '"underlying_need":"shared clarity about the date and added work",'
            '"emerging_delta":"the scope changed after the original agreement",'
            '"body_of_thought":"deadline and changed scope remain in tension"}\n'
            "Return JSON only."
        )}],
        max_tokens=300,
        parse=provider_bank._json_object,
        operation="hrn_relational",
    )

    assert result is None
    assert calls == [("groq", provider_bank.HRN_PROVIDER_CALL_TIMEOUT_SECONDS)]


def test_hrn_fast_failures_can_reach_third_candidate_inside_bounded_window(monkeypatch):
    candidates = [
        _item("groq", "openai/gpt-oss-120b"),
        _item("workers_ai", "@cf/google/gemma-4-26b-a4b-it"),
        _item("mistral", "mistral-small-latest"),
    ]
    _isolate_route(monkeypatch, candidates)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    good_response = json.dumps({
        "response": (
            "The agreed deadline and the changed scope are both present in the disagreement. "
            "One colleague is holding to the date while the other is pointing to the additional work. "
            "The exchange turns on how the original agreement relates to what was added."
        ),
        "question": "What happens in the conversation when the deadline is raised alongside the changed scope?",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    })

    def two_fast_failures_then_success(use_core, item, messages, max_tokens, schema, timeout_override=None):
        calls.append((item["provider"], timeout_override))
        if len(calls) < 3:
            clock.value += 1.7
            raise RuntimeError("simulated fast provider failure")
        return good_response

    monkeypatch.setattr(provider_bank, "_call", two_fast_failures_then_success)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": (
            "STRUCTURED MOVEMENT BRIEF\n"
            '{"working_hypothesis":"deadline disagreement",'
            '"underlying_need":"shared clarity about the date and added work",'
            '"emerging_delta":"the scope changed after the original agreement",'
            '"body_of_thought":"deadline and changed scope remain in tension"}\n'
            "Return JSON only."
        )}],
        max_tokens=300,
        parse=provider_bank._json_object,
        operation="hrn_relational",
    )

    assert provider_bank.HRN_RELATIONAL_FAST_FAILURE_WINDOW_SECONDS == 5.0
    assert result is not None
    assert result["provider"] == "mistral"
    assert calls == [
        ("groq", provider_bank.HRN_PROVIDER_CALL_TIMEOUT_SECONDS),
        ("workers_ai", provider_bank.HRN_PROVIDER_CALL_TIMEOUT_SECONDS),
        ("mistral", provider_bank.HRN_PROVIDER_CALL_TIMEOUT_SECONDS),
    ]
