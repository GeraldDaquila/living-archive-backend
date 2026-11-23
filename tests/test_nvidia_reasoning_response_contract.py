import provider_bank
import pytest


NVIDIA_LIGHTNING = "nvidia/nemotron-3.5-lightning-30b-a3b"
NVIDIA_SUPER_VL = "nvidia/nemotron-3.5-super-vl-120b-a12b"


def test_nvidia_super_vl_uses_documented_direct_answer_reasoning_control(monkeypatch):
    captured = {}

    def fake_http_json(url, headers, payload, provider, model, timeout=None):
        captured.update(payload)
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": '{"response":"A complete visitor-facing answer."}',
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"completion_tokens": 12},
        }

    monkeypatch.setattr(provider_bank, "_http_json", fake_http_json)

    result = provider_bank._openai_compatible(
        "https://integrate.api.nvidia.com/v1",
        "test-key",
        "nvidia",
        NVIDIA_SUPER_VL,
        [{"role": "user", "content": "Give a concise answer."}],
        750,
    )

    assert captured["reasoning_effort"] == "none"
    assert captured["chat_template_kwargs"] == {"enable_thinking": False}
    assert result.content == '{"response":"A complete visitor-facing answer."}'


def test_nvidia_lightning_keeps_thinking_disabled_without_unsupported_reasoning_effort(monkeypatch):
    captured = {}

    def fake_http_json(url, headers, payload, provider, model, timeout=None):
        captured.update(payload)
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": '{"response":"A complete visitor-facing answer."}',
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"completion_tokens": 12},
        }

    monkeypatch.setattr(provider_bank, "_http_json", fake_http_json)

    provider_bank._openai_compatible(
        "https://integrate.api.nvidia.com/v1",
        "test-key",
        "nvidia",
        NVIDIA_LIGHTNING,
        [{"role": "user", "content": "Give a concise answer."}],
        750,
    )

    assert captured["chat_template_kwargs"] == {"enable_thinking": False}
    assert "reasoning_effort" not in captured


def test_empty_nvidia_content_logs_only_response_shape_not_reasoning_text(monkeypatch, capsys):
    private_reasoning = "PRIVATE_REASONING_MUST_NOT_APPEAR_IN_LOGS"

    def fake_http_json(url, headers, payload, provider, model, timeout=None):
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "reasoning_content": private_reasoning,
                    },
                    "finish_reason": "length",
                }
            ],
            "usage": {
                "completion_tokens": 750,
                "completion_tokens_details": {"reasoning_tokens": 750},
            },
        }

    monkeypatch.setattr(provider_bank, "_http_json", fake_http_json)

    with pytest.raises(provider_bank.ProviderCallError) as error:
        provider_bank._openai_compatible(
            "https://integrate.api.nvidia.com/v1",
            "test-key",
            "nvidia",
            NVIDIA_LIGHTNING,
            [{"role": "user", "content": "Give a concise answer."}],
            750,
        )

    output = capsys.readouterr().out
    assert error.value.category == "invalid_provider_response"
    assert "finish_reason=length" in output
    assert "content_chars=0" in output
    assert "reasoning_content_present=True" in output
    assert "reasoning_tokens=750" in output
    assert private_reasoning not in output


def test_guide_arbitration_prefers_nvidia_super_vl_direct_answer_lane(monkeypatch):
    candidates = [
        {
            "provider": "nvidia",
            "model": NVIDIA_LIGHTNING,
            "health_state": "half_open",
            "last_success": 1_000,
            "transport_failures": 72,
            "consecutive_failures": 7,
            "quality_failures": 15,
            "latency_attempts": 0,
            "capabilities": ["composition", "low_latency"],
        },
        {
            "provider": "nvidia",
            "model": NVIDIA_SUPER_VL,
            "health_state": "half_open",
            "last_success": 2_000,
            "transport_failures": 76,
            "consecutive_failures": 3,
            "quality_failures": 11,
            "latency_attempts": 0,
            "capabilities": ["composition"],
        },
    ]
    state = dict(provider_bank._STATE)
    state["provider_cursor"] = 0
    state["model_cursors"] = {}
    monkeypatch.setattr(provider_bank, "_STATE", state)
    monkeypatch.setattr(provider_bank, "candidates", lambda *args, **kwargs: [dict(x) for x in candidates])

    selected = provider_bank.select(None, operation="general_guide_composition")

    assert selected[0]["model"] == NVIDIA_SUPER_VL
