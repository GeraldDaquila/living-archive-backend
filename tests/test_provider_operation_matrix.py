"""Provider gateway operation-matrix contract tests; no upstream calls."""
from unittest.mock import patch

import pytest
from fastapi import HTTPException

import provider_bank
import provider_gateway_service as gateway


def test_every_gateway_operation_has_provider_bank_contract_and_validates():
    assert gateway.ALLOWED_OPERATIONS
    for operation in sorted(gateway.ALLOWED_OPERATIONS):
        normalized, messages, max_tokens = gateway.validate_request({
            "contract_version": gateway.CONTRACT_VERSION,
            "operation": operation,
            "messages": [{"role": "user", "content": "Synthetic contract probe"}],
            "max_tokens": 1,
        })
        assert normalized == operation
        assert messages == [{"role": "user", "content": "Synthetic contract probe"}]
        assert max_tokens == 128
        assert operation in provider_bank.OPERATION_REQUIREMENTS
        assert operation in provider_bank.OPERATION_TOKEN_FLOORS
        assert provider_bank.OPERATION_TOKEN_FLOORS[operation] >= 128


def test_internal_guide_composition_lane_is_banked_but_not_gateway_exposed():
    operation = "general_guide_composition"
    assert operation in provider_bank.OPERATION_REQUIREMENTS
    assert operation in provider_bank.OPERATION_TOKEN_FLOORS
    assert operation not in gateway.ALLOWED_OPERATIONS


def test_voice_repair_uses_text_contract_and_preserves_operation():
    captured = {}

    def fake_route(**kwargs):
        captured.update(kwargs)
        return {
            "parsed": {"text": "Synthetic repaired voice."},
            "provider": "synthetic",
            "model": "synthetic-model",
            "preference_order": ["synthetic-model"],
        }

    with patch.object(gateway, "provider_bank_route", side_effect=fake_route):
        result = gateway.execute(
            operation="hrn_voice_repair",
            messages=[{"role": "user", "content": "Synthetic text"}],
            max_tokens=128,
            use_core=object(),
        )

    assert captured["operation"] == "hrn_voice_repair"
    assert captured["schema"] == {"mode": "text"}
    assert result["ok"] is True
    assert result["result"]["text"] == "Synthetic repaired voice."


def test_unknown_gateway_operation_fails_closed():
    with pytest.raises(HTTPException) as caught:
        gateway.validate_request({
            "contract_version": gateway.CONTRACT_VERSION,
            "operation": "unregistered_operation",
            "messages": [{"role": "user", "content": "Synthetic probe"}],
        })
    assert caught.value.status_code == 400
