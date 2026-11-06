"""Execution-boundary acceptance tests for USE specialists and Provider Bank.

All external boundaries are replaced with deterministic fakes. No provider,
WordPress, or Pinecone network calls are made.
"""
import json
from unittest.mock import patch

import pytest

import provider_gateway_service as gateway
from specialist_adapters import (
    SpecialistAdapterRegistry,
    SpecialistAdapterError,
    invoke_specialist,
)
from relationship_adapter import RelationshipAdapter
from philippine_systems_adapter import PhilippineSystemsAdapter
from formation_adapter import FormationAdapter
from safety_adapter import SafetyUtilityAdapter


def _context(specialist_id, question="Synthetic test inquiry", territory=""):
    from specialist_adapters import SpecialistAdapterContext
    return SpecialistAdapterContext(
        request_id="qa-execution-001",
        guide_version="qa",
        specialist_id=specialist_id,
        original_question=question,
        recognized_territory=territory,
        processing_purpose="deterministic QA",
        guide_context={"country": "Philippines"},
        safety_state="green",
    )


def _registry(*adapters):
    registry = SpecialistAdapterRegistry()
    for adapter in adapters:
        registry.register(adapter)
    return registry


def test_philippine_systems_adapter_executes_contribution_and_decline_paths():
    registry = _registry(PhilippineSystemsAdapter())
    relevant = invoke_specialist(
        registry,
        request_id="qa-ph-1", guide_version="qa",
        specialist_id="systems_ph",
        original_question="How do Philippine institutions and governance interact?",
        recognized_territory="Philippine systems",
        processing_purpose="qa",
    )
    assert relevant["status"] == "CONTRIBUTION"
    assert relevant["specialist_id"] == "systems_ph"
    assert relevant["canonical_candidates"][0]["url"].startswith("https://")

    declined = invoke_specialist(
        registry,
        request_id="qa-ph-2", guide_version="qa",
        specialist_id="systems_ph",
        original_question="How do I bake bread?",
        recognized_territory="food",
        processing_purpose="qa",
    )
    assert declined["status"] == "DECLINED"
    assert declined["canonical_candidates"] == []


def test_formation_adapter_executes_and_returns_bounded_canonical_doors():
    registry = _registry(FormationAdapter())
    result = invoke_specialist(
        registry,
        request_id="qa-formation-1", guide_version="qa",
        specialist_id="formation",
        original_question="I want to learn how to carry greater responsibility in stewardship.",
        recognized_territory="formation",
        processing_purpose="qa",
        guide_context={"situation": "learning and carrying responsibility"},
    )
    assert result["status"] == "CONTRIBUTION"
    assert result["specialist_id"] == "formation"
    assert len(result["canonical_candidates"]) <= 3
    assert result["boundary_notes"]["t4_destination_allowed"] is False


def test_relationship_adapter_executes_real_http_boundary_with_fake_transport():
    class FakeResponse:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self):
            return json.dumps({
                "ok": True,
                "response": "A synthetic relational response grounded in the supplied inquiry.",
                "clarity": "clear",
                "resources": [],
                "movement_state": "orientation",
                "question": "What part of the exchange remains unresolved?",
            }).encode()

    registry = _registry(RelationshipAdapter(endpoint="https://example.invalid/hrn", timeout=0.1))
    with patch("relationship_adapter.urllib.request.urlopen", return_value=FakeResponse()) as transport:
        result = invoke_specialist(
            registry,
            request_id="qa-relationship-1", guide_version="qa",
            specialist_id="relationship",
            original_question="We keep misunderstanding one another.",
            recognized_territory="relationship",
            processing_purpose="qa",
        )
    assert transport.call_count == 1
    assert result["status"] == "CONTRIBUTION"
    # The common v1 pipe intentionally carries the specialist-owned v2
    # contribution intact under payload; it does not flatten or rewrite it.
    assert result["payload"]["voice_policy"] == "preserve_specialist_voice"
    assert result["payload"]["human_response"].startswith("A synthetic relational response")
    assert result["payload"]["journey"]["display_mode"] == "hrn"


def test_relationship_adapter_retries_transient_http_failure_once():
    class FakeResponse:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self):
            return json.dumps({"ok": True, "response": "Synthetic response."}).encode()

    import urllib.error
    failure = urllib.error.HTTPError(
        "https://example.invalid/hrn", 503, "temporary", {}, None
    )
    registry = _registry(RelationshipAdapter(endpoint="https://example.invalid/hrn", timeout=0.1))
    with patch("relationship_adapter.urllib.request.urlopen", side_effect=[failure, FakeResponse()]) as transport, patch("relationship_adapter.time.sleep"):
        result = invoke_specialist(
            registry,
            request_id="qa-relationship-2", guide_version="qa",
            specialist_id="relationship",
            original_question="A synthetic relationship question.",
            recognized_territory="relationship",
            processing_purpose="qa",
        )
    assert transport.call_count == 2
    assert result["status"] == "CONTRIBUTION"


@pytest.mark.parametrize("operation", sorted(gateway.ALLOWED_OPERATIONS))
def test_gateway_executes_each_exposed_operation_through_bank_dispatch(operation):
    captured = {}

    def fake_route(**kwargs):
        captured.update(kwargs)
        raw = (
            "Synthetic repaired voice."
            if operation == "hrn_voice_repair"
            else json.dumps({"synthetic": True, "operation": operation})
        )
        parsed = kwargs["parse"](raw)
        return {
            "parsed": parsed,
            "provider": "synthetic",
            "model": "offline-fake",
            "preference_order": ["synthetic:offline-fake"],
        }

    messages = [{"role": "user", "content": "Synthetic execution probe"}]
    with patch.object(gateway, "provider_bank_route", side_effect=fake_route):
        result = gateway.execute(
            operation=operation,
            messages=messages,
            max_tokens=600,
            use_core=object(),
        )

    assert captured["operation"] == operation
    assert captured["messages"] == messages
    assert result["ok"] is True
    assert result["operation"] == operation
    assert result["provider"] == "synthetic"
    if operation == "hrn_voice_repair":
        assert captured["schema"] == {"mode": "text"}
        assert result["result"] == {"text": "Synthetic repaired voice."}
    else:
        assert result["result"] == {"synthetic": True, "operation": operation}


def test_safety_adapter_executes_deterministic_safety_handoff():
    registry = _registry(SafetyUtilityAdapter())
    result = invoke_specialist(
        registry,
        request_id="qa-safety-1", guide_version="qa",
        specialist_id="safety",
        original_question="I am thinking about hurting myself tonight and may act on it.",
        recognized_territory="immediate safety",
        processing_purpose="safety QA",
        guide_context={"country": "Philippines"},
        safety_state="acute",
    )
    assert result["status"] == "CONTRIBUTION"
    assert result["specialist_id"] == "safety"
    assert result["safety_flags"]["safety_interrupt"] is True
    assert result["boundary_notes"]["bypasses_llm"] is True
    assert result["payload"]["display_mode"] == "hrn_safety"


def test_gateway_returns_explicit_exhaustion_without_fabricating_success():
    with patch.object(gateway, "provider_bank_route", return_value=None):
        result = gateway.execute(
            operation="atlas_finder",
            messages=[{"role": "user", "content": "Synthetic probe"}],
            max_tokens=600,
            use_core=object(),
        )
    assert result["ok"] is False
    assert result["error"] == "provider_bank_exhausted"
