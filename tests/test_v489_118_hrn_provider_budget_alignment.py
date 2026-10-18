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


def test_hrn_slow_provider_failure_stops_before_extra_fallback(monkeypatch):
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
    assert calls == [
        ("workers_ai", provider_bank.HRN_GEMMA_4_26B_PROVIDER_CALL_TIMEOUT_SECONDS),
    ]
    assert provider_bank.HRN_GEMMA_4_26B_PROVIDER_CALL_TIMEOUT_SECONDS == 2.5


def test_hrn_fast_failures_stop_after_two_fallback_candidates(monkeypatch):
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
    assert provider_bank.HRN_RELATIONAL_FAST_FALLBACK_MAX_CANDIDATES == 2
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

def test_hrn_relational_tries_groq_120b_before_qwen_within_two_fallback_limit(monkeypatch):
    candidates = [
        _item("groq", "openai/gpt-oss-20b"),
        _item("openrouter", "google/gemma-4-31b-it:free"),
        _item("groq", "qwen/qwen3.8-27b"),
        _item("groq", "openai/gpt-oss-120b"),
    ]
    _isolate_route(monkeypatch, candidates)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    good_response = json.dumps({
        "response": (
            "You said you feel unheard when you and your colleague disagree. "
            "You want to understand what happens in those moments without assuming "
            "what your colleague intends. The difference between disagreeing about "
            "the topic and feeling unheard during the conversation is worth looking "
            "at separately."
        ),
        "question": (
            "When the disagreement starts, what do you notice first that tells you "
            "you are feeling unheard?"
        ),
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    })

    def fail_two_then_return_120b(use_core, item, messages, max_tokens, schema, timeout_override=None):
        provider_model = (item["provider"], item["model"])
        calls.append(provider_model)
        if provider_model != ("groq", "openai/gpt-oss-120b"):
            clock.value += 0.2
            raise RuntimeError("simulated provider failure")
        return good_response

    monkeypatch.setattr(provider_bank, "_call", fail_two_then_return_120b)
    result = provider_bank.route(
        use_core=None,
        messages=[{
            "role": "user",
            "content": (
                "STRUCTURED MOVEMENT BRIEF\n"
                '{"working_hypothesis":"the visitor feels unheard during disagreement with a colleague",'
                '"thread_summary":"the visitor wants to understand what happens during repeated disagreement",'
                '"underlying_need":"understand the interaction without assigning blame",'
                '"emerging_delta":"disagreeing about the topic differs from feeling unheard during the conversation",'
                '"body_of_thought":"the visitor feels unheard during disagreement with a colleague"}'
                "\nReturn JSON only."
            ),
        }],
        max_tokens=300,
        parse=provider_bank._json_object,
        operation="hrn_relational",
    )

    assert result is not None
    assert calls == [
        ("groq", "openai/gpt-oss-20b"),
        ("openrouter", "google/gemma-4-31b-it:free"),
        ("groq", "openai/gpt-oss-120b"),
    ]

def test_proven_workers_fast_fallback_keeps_groq_120b_inside_bounded_attempt_window(monkeypatch):
    workers = _item("workers_ai", "@cf/zai-org/glm-4.7-flash")
    # A half-open, recently successful lane is eligible for fast fallback but
    # must not displace the primary candidate.
    workers["health_state"] = "half_open"
    candidates = [
        _item("groq", "openai/gpt-oss-20b"),
        _item("openrouter", "google/gemma-4-31b-it:free"),
        _item("groq", "qwen/qwen3.8-27b"),
        _item("groq", "openai/gpt-oss-120b"),
        workers,
    ]
    _isolate_route(monkeypatch, candidates)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []
    good_response = json.dumps({
        "response": (
            "You said you feel unheard when you and your colleague disagree. "
            "You want to understand what happens in those moments without assuming "
            "what your colleague intends. The difference between disagreeing about "
            "the topic and feeling unheard during the conversation is worth looking "
            "at separately."
        ),
        "question": (
            "When the disagreement starts, what do you notice first that tells you "
            "you are feeling unheard?"
        ),
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    })

    def fail_until_groq_120b(use_core, item, messages, max_tokens, schema, timeout_override=None):
        candidate = (item["provider"], item["model"])
        calls.append(candidate)
        if candidate != ("groq", "openai/gpt-oss-120b"):
            clock.value += 0.2
            raise RuntimeError("simulated candidate failure")
        return good_response

    monkeypatch.setattr(provider_bank, "_call", fail_until_groq_120b)
    result = provider_bank.route(
        use_core=None,
        messages=[{
            "role": "user",
            "content": (
                "STRUCTURED MOVEMENT BRIEF\n"
                '{"working_hypothesis":"the visitor feels unheard during disagreement with a colleague",'
                '"thread_summary":"the visitor wants to understand what happens during repeated disagreement",'
                '"underlying_need":"understand the interaction without assigning blame",'
                '"emerging_delta":"disagreeing about the topic differs from feeling unheard during the conversation",'
                '"body_of_thought":"the visitor feels unheard during disagreement with a colleague"}'
                "\nReturn JSON only."
            ),
        }],
        max_tokens=300,
        parse=provider_bank._json_object,
        operation="hrn_relational",
    )

    assert result is not None
    assert calls == [
        ("groq", "openai/gpt-oss-20b"),
        ("workers_ai", "@cf/zai-org/glm-4.7-flash"),
        ("groq", "openai/gpt-oss-120b"),
    ]
