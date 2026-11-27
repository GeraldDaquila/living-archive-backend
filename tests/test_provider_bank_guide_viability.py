"""Regression coverage for bounded Guide provider arbitration and NVIDIA output."""

import pytest
import provider_bank


def test_guide_lane_prefers_recent_success_over_stale_model_preference(monkeypatch):
    candidates = [
        {
            "provider": "nvidia",
            "model": "nvidia/nemotron-3.5-super-vl-120b-a12b",
            "health_state": "healthy",
            "quality_failures": 0,
            "transport_failures": 0,
            "consecutive_failures": 0,
            "last_success": 0,
            "ewma_latency_seconds": 0,
            "latency_attempts": 0,
            "recent_timeouts": 0,
            "capabilities": ["composition", "relational_analysis"],
        },
        {
            "provider": "nvidia",
            "model": "nvidia/nemotron-3.5-lightning-30b-a3b",
            "health_state": "healthy",
            "quality_failures": 0,
            "transport_failures": 8,
            "consecutive_failures": 0,
            "last_success": 2000,
            "ewma_latency_seconds": 5.0,
            "latency_attempts": 1,
            "recent_timeouts": 0,
            "capabilities": ["composition", "relational_analysis", "low_latency"],
        },
    ]
    monkeypatch.setattr(provider_bank, "candidates", lambda *args, **kwargs: candidates)
    monkeypatch.setattr(provider_bank, "_csv", lambda _name: [])
    monkeypatch.setattr(provider_bank, "_provider_call_timeout", lambda *args, **kwargs: 5.0)
    monkeypatch.setattr(
        provider_bank,
        "_STATE",
        {"models": {}, "quality": {}, "provider_cursor": 0, "model_cursors": {}},
    )

    selected = provider_bank.select(object(), operation="general_guide_composition")

    assert selected[0]["model"] == "nvidia/nemotron-3.5-lightning-30b-a3b"


def test_openai_compatible_adapter_extracts_typed_text_blocks(monkeypatch):
    monkeypatch.setattr(
        provider_bank,
        "_http_json",
        lambda *args, **kwargs: {
            "choices": [{
                "message": {
                    "content": [
                        {"type": "reasoning", "text": "internal only"},
                        {"type": "text", "text": '{"response": '},
                        {"type": "output_text", "text": '"A grounded answer."}'},
                    ],
                    "reasoning_content": "must not be surfaced",
                },
                "finish_reason": "stop",
            }],
            "usage": {"completion_tokens": 42},
        },
    )

    output = provider_bank._openai_compatible(
        "https://api.nvidia.com/v1",
        "test-key",
        "nvidia",
        "nvidia/nemotron-3.5-lightning-30b-a3b",
        [{"role": "user", "content": "test"}],
        200,
        schema={"mode": "text"},
        timeout=5,
    )

    assert str(output) == '{"response": "A grounded answer."}'
    assert output.completion_tokens == 42


def test_openai_compatible_adapter_never_substitutes_reasoning_for_content(monkeypatch):
    monkeypatch.setattr(
        provider_bank,
        "_http_json",
        lambda *args, **kwargs: {
            "choices": [{
                "message": {
                    "content": None,
                    "reasoning_content": "private reasoning without an answer",
                },
                "finish_reason": "stop",
            }],
        },
    )

    with pytest.raises(provider_bank.ProviderCallError) as error:
        provider_bank._openai_compatible(
            "https://api.nvidia.com/v1",
            "test-key",
            "nvidia",
            "nvidia/nemotron-3.5-lightning-30b-a3b",
            [{"role": "user", "content": "test"}],
            200,
            schema={"mode": "text"},
            timeout=5,
        )

    assert error.value.category == "invalid_provider_response"


def test_humility_contract_rejection_is_task_specific_not_global_provider_quality_failure():
    reason = (
        "humility/spiritual-maturity answer is incomplete: "
        "relationship_mechanism,preserves_appropriate_boundaries"
    )
    assert provider_bank._contract_rejection_class(reason) == "task_specific_completeness"
    assert provider_bank._contract_rejection_reason_code(reason) == (
        "humility_spiritual_maturity_incomplete_relationship_mechanism_"
        "preserves_appropriate_boundaries"
    )


def test_humility_contract_rejection_reason_code_is_bounded_and_content_free():
    reason = (
        "humility/spiritual-maturity answer is incomplete: "
        "relationship_mechanism,not_passivity_or_automatic_compliance"
    )
    code = provider_bank._contract_rejection_reason_code(reason)
    assert code == (
        "humility_spiritual_maturity_incomplete_relationship_mechanism_"
        "not_passivity_or_automatic_compliance"
    )
    assert "humility" in code
    assert "provider response text" not in code



def test_parser_contract_rejection_enters_bounded_same_model_repair(monkeypatch):
    candidate = {
        "provider": "test_provider",
        "model": "test-model",
        "health_state": "healthy",
        "quality_failures": 0,
        "transport_failures": 0,
        "consecutive_failures": 0,
        "last_success": 0,
        "capabilities": ["composition", "json_schema_strict"],
    }
    state = {"state": "healthy", "probe_in_flight": False}
    raw_outputs = iter(("first-output", "repaired-output"))
    provider_messages = []
    parser_calls = []

    monkeypatch.setattr(provider_bank, "_active_active_primary_assignment", lambda *args: False)
    monkeypatch.setattr(provider_bank, "_current_gold_star_evaluation_context", lambda: None)
    monkeypatch.setattr(
        provider_bank,
        "_bounded_request_provider_timeout",
        lambda timeout, _deadline, **kwargs: timeout,
    )
    monkeypatch.setattr(provider_bank, "_active_active_role", lambda: "secondary")
    monkeypatch.setattr(provider_bank, "refresh_server_capacity_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "select", lambda *args, **kwargs: [candidate])
    monkeypatch.setattr(provider_bank, "provider_input_exceeds_tpm_budget", lambda *args, **kwargs: None)
    monkeypatch.setattr(provider_bank, "_capacity_begin_request", lambda: None)
    monkeypatch.setattr(provider_bank, "_capacity_end_request", lambda **kwargs: None)
    monkeypatch.setattr(provider_bank, "_state", lambda *args: state)
    monkeypatch.setattr(provider_bank, "_blocked_for_operation", lambda *args, **kwargs: False)
    monkeypatch.setattr(provider_bank, "acquire_probe", lambda _state: True)
    monkeypatch.setattr(provider_bank, "_provider_call_timeout", lambda *args, **kwargs: 8.0)
    monkeypatch.setattr(provider_bank, "_capabilities", lambda *args, **kwargs: {"json_schema_strict"})
    monkeypatch.setattr(provider_bank, "_normalize_operation_result", lambda operation, parsed, **kwargs: parsed)
    monkeypatch.setattr(provider_bank, "_record_predictive_shadow", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        provider_bank,
        "_predictive_shadow_metrics",
        lambda *args, **kwargs: {
            "ewma_latency_seconds": 1.0,
            "timeout_risk": 0.0,
            "deadline_fit": True,
        },
    )
    monkeypatch.setattr(provider_bank, "_success", lambda *args, **kwargs: None)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: None)
    monkeypatch.setattr(
        provider_bank,
        "_quota_guarded_call",
        lambda _core, _item, messages, *_args, **_kwargs: (
            provider_messages.append(messages) or next(raw_outputs)
        ),
    )
    monkeypatch.setattr(
        provider_bank._gold_star_trace,
        "set_provider_route_candidate_count",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        provider_bank._gold_star_trace,
        "record_provider_candidate_outcome",
        lambda *args, **kwargs: None,
    )

    def parse(raw):
        parser_calls.append(raw)
        if raw == "first-output":
            raise ValueError(
                "humility/spiritual-maturity answer is incomplete: "
                "humility_supports_learning_and_correction,"
                "not_passivity_or_automatic_compliance"
            )
        return {"response": "A corrected, complete visitor answer."}

    result = provider_bank.route(
        use_core=object(),
        messages=[{"role": "user", "content": "What is the relationship between humility and spiritual maturity?"}],
        max_tokens=750,
        parse=parse,
        operation="general_guide_composition",
    )

    assert result["parsed"]["response"] == "A corrected, complete visitor answer."
    assert result["provider"] == "test_provider"
    assert result["model"] == "test-model"
    assert parser_calls == ["first-output", "repaired-output"]
    assert len(provider_messages) == 2
    assert any(
        "Your preceding Guide answer omitted required humility/spiritual-maturity distinctions" in message.get("content", "")
        for message in provider_messages[1]
        if message.get("role") == "user"
    )
    assert any(
        "willingness to learn" in message.get("content", "")
        and "automatic compliance" in message.get("content", "")
        for message in provider_messages[1]
        if message.get("role") == "user"
    )


def test_humility_contract_repair_instruction_expands_only_missing_dimensions():
    instruction = provider_bank._guide_contract_repair_instruction(
        "humility/spiritual-maturity answer is incomplete: "
        "humility_supports_learning_and_correction,not_passivity_or_automatic_compliance,"
        "not_self_erasure_or_self_contempt"
    )
    assert instruction is not None
    assert "willingness to learn" in instruction
    assert "honest self-appraisal" in instruction
    assert "accepting correction" in instruction
    assert "blind obedience" in instruction
    assert "State explicitly that humility is not self-erasure" in instruction
    assert "automatic compliance" in instruction
    assert "State explicitly that humility is not passivity" in instruction
    assert "appropriate boundaries" not in instruction
    assert provider_bank._guide_contract_repair_instruction(
        "unrelated provider failure"
    ) is None
