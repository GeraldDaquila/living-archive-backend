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
    elif operation == "safety_conversation":
        # Safety is deterministic and intentionally bypasses provider JSON parsing.
        assert result["result"] == {"text": json.dumps({"synthetic": True, "operation": operation})}
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
    assert result["payload"]["display_mode"] == "safety"


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


# These tests call provider_bank.route itself. Only candidate discovery, transport,
# quota reservation, and shared persistence are replaced; arbitration, parsing,
# failure classification, health transitions, and fallback remain real.
def _offline_bank_patches(bank, candidates, call_side_effect):
    class Reservation:
        def settle_output(self, result): pass
        def release(self): pass

    return (
        patch.object(bank, "_sync_shared_state"),
        patch.object(bank, "_persist_shared_state"),
        patch.object(bank, "select", return_value=candidates),
        patch.object(bank, "_call", side_effect=call_side_effect),
        patch.object(bank, "reserve_provider_call", return_value=Reservation()),
    )


def test_provider_bank_real_route_retries_independent_candidate_after_invalid_json():
    import provider_bank as bank

    candidates = [
        {"provider": "groq", "model": "synthetic-primary"},
        {"provider": "mistral", "model": "synthetic-fallback"},
    ]
    calls = []

    def fake_call(use_core, item, messages, max_tokens, schema=None, timeout_override=None):
        calls.append((item["provider"], item["model"], max_tokens, timeout_override))
        if item["provider"] == "groq":
            return "not-json"
        return json.dumps({"answer": "synthetic fallback accepted"})

    patches = _offline_bank_patches(bank, candidates, fake_call)
    with patches[0], patches[1], patches[2], patches[3], patches[4]:
        result = bank.route(
            use_core=object(),
            messages=[{"role": "user", "content": "Synthetic route test"}],
            max_tokens=100,
            parse=json.loads,
            operation="generic",
        )

    assert result["provider"] == "mistral"
    assert result["model"] == "synthetic-fallback"
    assert result["parsed"] == {"answer": "synthetic fallback accepted"}
    assert [entry[0] for entry in calls] == ["groq", "mistral"]
    assert all(entry[2] >= 100 for entry in calls)


def test_provider_bank_real_route_skips_candidate_blocked_during_arbitration():
    import provider_bank as bank

    candidates = [
        {"provider": "groq", "model": "synthetic-blocked"},
        {"provider": "mistral", "model": "synthetic-healthy"},
    ]
    calls = []

    def fake_call(use_core, item, messages, max_tokens, schema=None, timeout_override=None):
        calls.append(item["provider"])
        return json.dumps({"answer": "healthy lane"})

    patches = _offline_bank_patches(bank, candidates, fake_call)
    with (patches[0], patches[1], patches[2], patches[3], patches[4],
          patch.object(bank, "_blocked_for_operation", side_effect=[True, False])):
        result = bank.route(
            use_core=object(),
            messages=[{"role": "user", "content": "Synthetic blocked-candidate test"}],
            max_tokens=100,
            parse=json.loads,
            operation="generic",
        )

    assert result["provider"] == "mistral"
    assert calls == ["mistral"]


def test_provider_bank_real_route_returns_none_when_all_candidates_fail():
    import provider_bank as bank

    candidates = [
        {"provider": "groq", "model": "synthetic-one"},
        {"provider": "mistral", "model": "synthetic-two"},
    ]

    def fake_call(use_core, item, messages, max_tokens, schema=None, timeout_override=None):
        raise RuntimeError("synthetic transport outage")

    patches = _offline_bank_patches(bank, candidates, fake_call)
    with patches[0], patches[1], patches[2], patches[3], patches[4]:
        result = bank.route(
            use_core=object(),
            messages=[{"role": "user", "content": "Synthetic exhaustion test"}],
            max_tokens=100,
            parse=json.loads,
            operation="generic",
        )

    assert result is None


def test_relationship_is_native_guide_contribution_after_hrn_redesign():
    import main as guide
    assert not hasattr(guide, "_relationship_specialist_response")

def test_guide_formation_specialist_integration_preserves_domain_payload():
    import main as guide

    result = guide._formation_specialist_response(
        "I want to carry greater responsibility in stewardship.",
        [],
        {"round1_interpretation": {
            "presenting_situation": "learning to carry responsibility",
            "desired_movement": "greater stewardship capacity",
        }},
        "qa-guide-formation-001",
    )

    delegation = result["formation_delegation"]
    assert delegation["state"] == "open"
    assert delegation["specialist_id"] == "formation"
    assert delegation["return_mode"] == "guide_integrated"
    assert isinstance(delegation["interpretation"], dict)
    assert isinstance(delegation["movement"], dict)
    assert len(delegation["doors"]) <= 3
