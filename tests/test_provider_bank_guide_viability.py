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
