"""Current specialist-pipe regression probes.

These probes exercise two failure seams that previously could pass structural
checks while failing in production:
1. domain-specific specialist payload preservation through the common pipe;
2. transient HRN transport failure recovery at the Relationship adapter.
"""

from pathlib import Path
from unittest.mock import patch
import json
import urllib.error

import provider_bank

from relationship_adapter import RelationshipAdapter
from specialist_adapters import (
    SpecialistAdapterContext,
    SpecialistAdapterRegistry,
    invoke_specialist,
)


ROOT = Path(__file__).resolve().parents[1]


class _FakeFormationAdapter:
    specialist_id = "formation"

    def process(self, context):
        return {
            "contract_version": "formation-v1",
            "request_id": context.request_id,
            "specialist_id": "formation",
            "status": "CONTRIBUTION",
            "voice_policy": "preserve_specialist_boundary",
            "interpretation": {
                "pathway": "The responsibility is changing shape.",
                "signals": {"responsibility_transition": True},
            },
            "movement": {"direction": "formation"},
            "canonical_candidates": [
                {
                    "id": "learning_arcs",
                    "title": "Learning Arcs",
                    "url": "https://geralddaquila.com/steward-access-12-learning-arcs/",
                }
            ],
            "boundary_notes": {"t4_destination_allowed": False},
            "safety_flags": {"safety_state": "green"},
        }


class _Response:
    def __init__(self, status, payload):
        self.status = status
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_domain_payload_survives_common_pipe():
    registry = SpecialistAdapterRegistry()
    registry.register(_FakeFormationAdapter())

    result = invoke_specialist(
        registry,
        request_id="qa-formation-payload-001",
        guide_version="qa-current",
        specialist_id="formation",
        original_question="I am carrying a larger responsibility.",
        recognized_territory="stewardship formation",
        processing_purpose="bounded formation navigation",
        guide_context={"situation": "A responsibility is changing."},
        safety_state="green",
    )

    assert result["status"] == "CONTRIBUTION"
    assert result["payload"]["interpretation"]["pathway"] == (
        "The responsibility is changing shape."
    )
    assert result["payload"]["movement"]["direction"] == "formation"
    assert result["canonical_candidates"][0]["id"] == "learning_arcs"


def test_relationship_adapter_retries_transient_503():
    adapter = RelationshipAdapter(endpoint="https://example.test/hrn", timeout=1.0)
    context = SpecialistAdapterContext(
        request_id="qa-hrn-retry-001",
        guide_version="v487.91",
        specialist_id="relationship",
        original_question="Something feels different between us.",
        recognized_territory="human relationships",
        processing_purpose="open relational exploration",
        guide_context={"conversation": ""},
        safety_state="green",
    )

    calls = {"count": 0}

    def fake_urlopen(request, timeout):
        calls["count"] += 1
        if calls["count"] == 1:
            body = json.dumps(
                {"ok": False, "retryable": True, "error": "transient composition failure"}
            ).encode("utf-8")
            raise urllib.error.HTTPError(
                request.full_url,
                503,
                "Service Unavailable",
                {},
                __import__("io").BytesIO(body),
            )
        return _Response(
            200,
            {
                "ok": True,
                "response": "There is something worth noticing in what is happening between you.",
                "clarity": "relational pattern",
                "movement_state": "explore",
                "resources": [],
            },
        )

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        result = adapter.process(context)

    assert calls["count"] == 2
    assert result["status"] == "CONTRIBUTION"
    assert result["human_response"].startswith("There is something worth noticing")
    assert result["voice_policy"] == "preserve_specialist_voice"







def test_hrn_contract_trims_only_incomplete_trailing_sentence():
    parsed = {
        "response": "The first distinction is clear. The next sentence starts but does not finish",
        "question": "What stands out to you?",
    }
    normalized = provider_bank._normalize_operation_result("hrn_relational", parsed)
    assert normalized["response"] == "The first distinction is clear."
    assert normalized["response"].endswith(".")



def test_hrn_contract_recovery_falls_back_to_json_object_without_schema_capability():
    original = [{"role": "user", "content": "Someone I love has become distant."}]
    incomplete = json.dumps({
        "response": "This begins clearly but stops before the sentence is complete",
        "question": "What feels hardest?",
    })
    corrected = json.dumps({
        "response": "This is a complete and grounded observation.",
        "question": "What feels different when you consider that?",
    })
    pool = [{"provider": "groq", "model": "qwen-test", "index": 0}]

    with (
        patch.object(provider_bank, "select", return_value=pool),
        patch.object(provider_bank, "_call", side_effect=[incomplete, corrected]) as provider_call,
        patch.object(provider_bank, "_state", return_value={"state": "healthy"}),
        patch.object(provider_bank, "acquire_probe", return_value=True),
        patch.object(provider_bank, "_success"),
        patch.object(provider_bank, "_capabilities", return_value=frozenset({"json_object"})),
    ):
        result = provider_bank.route(
            use_core=None, messages=original, max_tokens=600,
            parse=json.loads, operation="hrn_relational",
        )

    assert result["parsed"]["response"].endswith(".")
    assert provider_call.call_count == 2
    assert provider_call.call_args_list[1].args[4] is None
    recovery_messages = provider_call.call_args_list[1].args[2]
    assert "complete response" in recovery_messages[-1]["content"]
    assert "end with sentence-final punctuation" in recovery_messages[-1]["content"]



def test_hrn_contract_rejects_truncated_response():
    incomplete = {
        "response": "This begins clearly but stops before the sentence is complete",
        "question": "What stands out to you?",
    }
    try:
        provider_bank._normalize_operation_result("hrn_relational", incomplete)
    except ValueError as exc:
        assert "complete response" in str(exc)
    else:
        raise AssertionError("incomplete HRN response should be rejected")

    complete = {
        "response": "This is a complete observation. The thought has landed.",
        "question": "What stands out to you?",
    }
    normalized = provider_bank._normalize_operation_result("hrn_relational", complete)
    assert normalized["response"].endswith(".")



def test_json_object_instruction_is_added_at_provider_boundary():
    messages = [{"role": "user", "content": "Explain the situation plainly."}]
    effective = provider_bank._ensure_json_object_instruction(messages, None)
    assert effective[0]["role"] == "system"
    assert "json object" in effective[0]["content"].casefold()
    assert messages == [{"role": "user", "content": "Explain the situation plainly."}]

    text_messages = [{"role": "user", "content": "Write a short sentence."}]
    assert provider_bank._ensure_json_object_instruction(
        text_messages, {"mode": "text"}
    ) is text_messages

    existing = [{"role": "system", "content": "Return valid JSON."}]
    assert provider_bank._ensure_json_object_instruction(existing, None) is existing



def test_hrn_contract_recovery_corrects_rejected_provider_output():
    original = [{"role": "user", "content": "Someone I love has become distant."}]
    rejected = json.dumps({"question": "What feels hardest?", "rest": False})
    corrected = json.dumps({
        "response": "You are trying to respect their space without letting the distance speak for you.",
        "question": "What makes reaching out feel risky right now?",
    })
    pool = [{"provider": "groq", "model": "test-model", "index": 0}]

    with (
        patch.object(provider_bank, "select", return_value=pool),
        patch.object(provider_bank, "_call", side_effect=[rejected, corrected]) as provider_call,
        patch.object(provider_bank, "_state", return_value={"state": "healthy"}),
        patch.object(provider_bank, "acquire_probe", return_value=True),
        patch.object(provider_bank, "_success"),
        patch.object(provider_bank, "_capabilities", return_value=frozenset({"json_schema_best_effort"})),
    ):
        result = provider_bank.route(
            use_core=None,
            messages=original,
            max_tokens=600,
            parse=json.loads,
            operation="hrn_relational",
        )

    assert result["parsed"]["response"] == (
        "You are trying to respect their space without letting the distance speak for you."
    )
    assert result["parsed"]["question"] == "What makes reaching out feel risky right now?"
    assert provider_call.call_count == 2
    recovery_messages = provider_call.call_args_list[1].args[2]
    assert any(message.get("role") == "user" and message.get("content") == original[0]["content"] for message in recovery_messages)
    assert recovery_messages[-2] == {"role": "assistant", "content": rejected}
    assert "requires response" in recovery_messages[-1]["content"]
    assert "Correct the output now." in recovery_messages[-1]["content"]
    assert original == [{"role": "user", "content": "Someone I love has become distant."}]


def test_current_main_contains_domain_payload_consumption_guards():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert 'APP_VERSION = "v489.40"' in source
    assert "domain_payload = dict(hub_contribution.payload or {})" in source
    assert "interpretation_data = dict(domain_payload.get(\"interpretation\") or {})" in source
    assert "domain_payload = dict(contribution.get(\"payload\") or {})" in source
    assert "interpretation = dict(domain_payload.get(\"interpretation\") or {})" in source
    provider_bank_source = (ROOT / "provider_bank.py").read_text(encoding="utf-8")
    assert "raw_output = _call(use_core, item, effective_messages, effective_max_tokens, effective_schema)" in provider_bank_source
    assert "recovery_messages.append({" in provider_bank_source
    assert "Correct the output now." in provider_bank_source


if __name__ == "__main__":
    test_domain_payload_survives_common_pipe()
    test_relationship_adapter_retries_transient_503()
    test_hrn_contract_recovery_corrects_rejected_provider_output()
    test_json_object_instruction_is_added_at_provider_boundary()
    test_hrn_contract_rejects_truncated_response()
    test_hrn_contract_recovery_falls_back_to_json_object_without_schema_capability()
    test_hrn_contract_trims_only_incomplete_trailing_sentence()
    test_current_main_contains_domain_payload_consumption_guards()
    print("current specialist-pipe regression probes: PASS")
