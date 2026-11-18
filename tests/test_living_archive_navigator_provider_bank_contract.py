from provider_gateway_service import ALLOWED_OPERATIONS, validate_request
from provider_bank import OPERATION_REQUIREMENTS, OPERATION_TOKEN_FLOORS, _operation_requirements


def test_living_archive_navigator_is_an_explicit_provider_gateway_operation():
    assert "living_archive_navigator" in ALLOWED_OPERATIONS
    operation, messages, max_tokens = validate_request({
        "contract_version": "v1",
        "operation": "living_archive_navigator",
        "messages": [
            {"role": "system", "content": "Interpret the visitor's question."},
            {"role": "user", "content": "I want to understand what changed."},
        ],
        "max_tokens": 1500,
        "schema": {
            "type": "object",
            "properties": {"situation": {"type": "string"}},
            "required": ["situation"],
            "additionalProperties": False,
        },
    })
    assert operation == "living_archive_navigator"
    assert len(messages) == 2
    assert max_tokens == 1500


def test_living_archive_navigator_uses_provider_bank_capability_and_budget_policy():
    required = OPERATION_REQUIREMENTS["living_archive_navigator"]
    assert required == frozenset({"json_object", "long_context", "reasoning", "composition"})
    assert OPERATION_TOKEN_FLOORS["living_archive_navigator"] == 900
    assert _operation_requirements("living_archive_navigator", None) == set(required)


def test_living_archive_navigator_rejects_unknown_or_invalid_contract():
    try:
        validate_request({
            "contract_version": "v1",
            "operation": "living_archive_navigator_direct_groq",
            "messages": [{"role": "user", "content": "Hello"}],
        })
    except Exception as exc:
        assert "Unsupported Provider Bank operation" in str(exc)
    else:
        raise AssertionError("Unknown operation was not rejected")


def test_living_archive_navigator_uses_bounded_provider_attempts():
    from provider_bank import _provider_call_timeout

    assert _provider_call_timeout("living_archive_navigator", {"provider": "workers_ai", "model": "@cf/google/gemma-4-26b-a4b-it"}) == 4.0
    assert _provider_call_timeout("living_archive_navigator", {"provider": "groq", "model": "openai/gpt-oss-120b"}) == 4.0
