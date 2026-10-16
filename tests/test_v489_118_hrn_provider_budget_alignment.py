"""Regression tests for HRN provider-budget alignment.

These tests are deterministic and never call an external provider.
"""
import json

import pytest
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
        messages=[{
            "role": "user",
            "content": (
                "STRUCTURED MOVEMENT BRIEF\n"
                '{"working_hypothesis":"friend disagreement leaves the visitor feeling unheard",'
                '"thread_summary":"the visitor feels unheard during disagreement with a friend",'
                '"underlying_need":"understand what happens when disagreement begins",'
                '"emerging_delta":"feeling unheard during the conversation differs from disagreeing about the topic",'
                '"body_of_thought":"the disagreement and feeling unheard are related but not identical"}'
                "\nReturn JSON only."
            ),
        }],
        max_tokens=300,
        parse=provider_bank._json_object,
        operation="hrn_relational",
    )

    assert result is None
    # A six-second elapsed failure exceeds the 4.5-second budget, so no
    # mirror candidate is attempted after the slow primary lane.
    assert calls == [
        ("workers_ai", provider_bank.HRN_GEMMA_4_26B_PROVIDER_CALL_TIMEOUT_SECONDS),
    ]


def test_hrn_fast_failures_stop_before_third_candidate_when_budget_is_exhausted(monkeypatch):
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
            "You said you feel unheard when you and your friend disagree. "
            "You want to understand what happens in those moments without assuming "
            "what your friend intends. The difference between disagreeing about a "
            "topic and feeling unheard during the conversation is worth looking at separately."
        ),
        "question": "Can you share a recent example of a disagreement where you felt unheard?",
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
        messages=[{
            "role": "user",
            "content": (
                "STRUCTURED MOVEMENT BRIEF\\n"
                '{"working_hypothesis":"friend disagreement leaves the visitor feeling unheard",'
                '"thread_summary":"the visitor feels unheard during disagreement with a friend",'
                '"underlying_need":"understand what happens when disagreement begins",'
                '"emerging_delta":"feeling unheard during the conversation differs from disagreeing about the topic",'
                '"body_of_thought":"the disagreement and feeling unheard are related but not identical"}'
                "\\nReturn JSON only."
            ),
        }],
        max_tokens=300,
        parse=provider_bank._json_object,
        operation="hrn_relational",
    )

    assert provider_bank.HRN_RELATIONAL_FAST_FAILURE_WINDOW_SECONDS == 4.5
    assert result is None
    assert calls == [
        ("workers_ai", provider_bank.HRN_GEMMA_4_26B_PROVIDER_CALL_TIMEOUT_SECONDS),
        ("groq", provider_bank.HRN_PROVIDER_CALL_TIMEOUT_SECONDS),
    ]



def test_workers_text_transport_flattens_text_parts_and_omits_invalid_text_response_format(monkeypatch):
    captured = {}

    def fake_http_json(url, headers, payload, provider, model, timeout=None):
        captured.update(payload)
        return {"result": {"response": "plain response"}}

    monkeypatch.setattr(provider_bank, "_http_json", fake_http_json)
    result = provider_bank._workers(
        "token", "account", "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
        [
            {"role": "system", "content": [{"type": "text", "text": "Return one JSON object."}]},
            {"role": "user", "content": [{"type": "text", "text": "Describe the interaction."}]},
        ],
        250,
        schema={"mode": "text"},
        timeout=1.0,
    )

    assert result == "plain response"
    assert captured["messages"] == [
        {"role": "system", "content": "Return one JSON object."},
        {"role": "user", "content": "Describe the interaction."},
    ]
    assert "response_format" not in captured
    assert captured["options"] == {"rejectIfBusy": True}


def test_workers_json_transport_uses_supported_json_response_format(monkeypatch):
    captured = {}

    def fake_http_json(url, headers, payload, provider, model, timeout=None):
        captured.update(payload)
        return {"result": {"response": '{"ok":true}'}}

    monkeypatch.setattr(provider_bank, "_http_json", fake_http_json)
    result = provider_bank._workers(
        "token", "account", "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
        [{"role": "user", "content": "Return JSON."}],
        250,
        schema=None,
        timeout=1.0,
    )

    assert result == '{"ok":true}'
    assert captured["response_format"] == {"type": "json_object"}
    assert captured["response_format"]["type"] != "text"


def test_workers_text_transport_rejects_multimodal_parts_instead_of_silently_dropping_them():
    with pytest.raises(provider_bank.ProviderCallError) as exc:
        provider_bank._workers_normalize_messages(
            [{"role": "user", "content": [
                {"type": "text", "text": "Describe this image."},
                {"type": "image_url", "image_url": {"url": "https://example.com/image.png"}},
            ]}],
            "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
        )

    assert exc.value.category == "unsupported_request"


def test_action_guidance_contract_failure_skips_same_model_rewrite_and_uses_independent_candidate(monkeypatch):
    candidates = [
        _item("groq", "qwen/qwen3.8-27b"),
        _item("mistral", "mistral-small-latest"),
    ]
    _isolate_route(monkeypatch, candidates)
    calls = []

    rejected = json.dumps({
        "response": (
            "You described a recurring imbalance in the friendship. "
            "You should discuss expectations with your friend and agree on a fairer division. "
            "This may help both of you understand what each person contributes."
        ),
        "question": "What would change if you discussed expectations directly?",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    })
    accepted = json.dumps({
        "response": (
            "You described being the one who often makes the effort, while also wanting to be fair to your friend. "
            "Those two parts of your account can both be true: the effort may feel uneven, and you may still be unsure "
            "what explains the difference. What your friend is experiencing remains unknown from this account alone."
        ),
        "question": "Can you recall a recent moment when you were the one who reached out?",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    })

    def fake_call(use_core, item, messages, max_tokens, schema, timeout_override=None):
        calls.append((item["provider"], item["model"]))
        return rejected if item["provider"] == "groq" else accepted

    monkeypatch.setattr(provider_bank, "_quota_guarded_call", fake_call)
    original_normalize = provider_bank._normalize_operation_result

    def reject_action_guidance(operation, parsed, messages=None):
        if operation == "hrn_relational" and parsed.get("response", "").startswith("You described a recurring imbalance"):
            raise ValueError("hrn_relational visitor-surface contract violation: action-guidance")
        return original_normalize(operation, parsed, messages=messages)

    monkeypatch.setattr(provider_bank, "_normalize_operation_result", reject_action_guidance)
    result = provider_bank.route(
        use_core=None,
        messages=[{
            "role": "user",
            "content": (
                "STRUCTURED MOVEMENT BRIEF\n"
                '{"working_hypothesis":"visitor feels effort is uneven but does not want to judge friend",'
                '"thread_summary":"visitor often initiates effort in a friendship",'
                '"underlying_need":"understand the perceived imbalance fairly",'
                '"emerging_delta":"feeling uneven effort does not establish the friend\'s intentions",'
                '"body_of_thought":"the visitor reports initiating effort and remains uncertain about the friend\'s perspective"}'
                "\nReturn JSON only."
            ),
        }],
        max_tokens=300,
        parse=provider_bank._json_object,
        operation="hrn_relational",
    )

    assert result is not None
    assert result["provider"] == "mistral"
    assert calls == [
        ("groq", "qwen/qwen3.8-27b"),
        ("mistral", "mistral-small-latest"),
    ]
