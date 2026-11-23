from types import SimpleNamespace

import pytest

import provider_bank


class _FakeGroqClient:
    def __init__(self, response):
        self.response = response
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

    def with_options(self, **kwargs):
        assert kwargs["max_retries"] == 0
        return self

    def _create(self, **kwargs):
        return self.response


def test_groq_empty_content_logs_shape_only_and_fails_closed(capsys):
    private_reasoning = "this must never appear in diagnostics"
    message = SimpleNamespace(
        content=None,
        reasoning=private_reasoning,
        reasoning_content=None,
        model_fields_set={"content", "reasoning"},
    )
    usage = SimpleNamespace(
        completion_tokens=750,
        completion_tokens_details=SimpleNamespace(reasoning_tokens=750),
    )
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=message, finish_reason="length")],
        usage=usage,
    )
    core = SimpleNamespace(groq_client=_FakeGroqClient(response))

    with pytest.raises(provider_bank.ProviderCallError) as caught:
        provider_bank._groq(
            core,
            "openai/gpt-oss-120b",
            [{"role": "user", "content": "Synthetic prompt"}],
            750,
            schema={"type": "object"},
            timeout=5,
        )

    assert caught.value.category == "invalid_provider_response"
    output = capsys.readouterr().out
    assert "provider=groq" in output
    assert "finish_reason=length" in output
    assert "reasoning_present=True" in output
    assert "reasoning_tokens=750" in output
    assert private_reasoning not in output
