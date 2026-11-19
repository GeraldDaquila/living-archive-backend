"""Tests for the shared Gold Star v2 answer-envelope contract."""
from gold_star_answer_envelope import (
    VERSION,
    build_answer_envelope,
    validate_answer_envelope,
)
from gold_star_question_contract import build_question_contract
from gold_star_response_floor import evaluate_response_floor


def test_completed_answer_envelope_separates_route_provenance_and_doorway():
    query = "What is photosynthesis?"
    payload = {
        "ok": True,
        "query": query,
        "response": "Photosynthesis converts light energy into chemical energy.",
        "route_source": "guide_basic_inquiry",
        "provider": "provider-bank",
        "model": "model-a",
        "response_provenance": {"class": "llm"},
        "recommendation": {"title": "Plant biology", "url": "https://example.org/plants"},
    }
    envelope = build_answer_envelope(query, payload, build_question_contract(query))
    assert envelope["version"] == VERSION
    assert envelope["state"] == "completed_answer"
    assert envelope["route"]["class"] == "guide_composition"
    assert envelope["route"]["provider_present"] is True
    assert envelope["evidence"]["provenance_class"] == "llm"
    assert envelope["doorway"]["separate_from_answer"] is True
    assert envelope["capability"]["semantic_competence_certified"] is False
    assert validate_answer_envelope(envelope)["valid"] is True


def test_unregistered_route_and_missing_capability_declaration_remain_unknown():
    query = "Explain a complex issue."
    payload = {"ok": True, "response": "A bounded answer.", "route_source": "new_route_not_yet_registered"}
    envelope = build_answer_envelope(query, payload, build_question_contract(query))
    assert envelope["route"]["class"] == "unclassified"
    assert envelope["capability"]["declaration_status"] == "not_declared"
    assert envelope["capability"]["supported_task_families"] == []
    assert envelope["capability"]["semantic_competence_certified"] is False


def test_structured_handoff_is_not_mislabeled_as_completed_answer():
    query = "Find the catalogue."
    payload = {"ok": True, "handoff": "catalogue", "handoff_pending": True, "response": ""}
    envelope = build_answer_envelope(query, payload, build_question_contract(query))
    assert envelope["state"] == "structured_handoff"


def test_explicit_no_handoff_constraint_is_preserved_in_envelope():
    query = "Explain this without links or resources."
    envelope = build_answer_envelope(
        query,
        {"ok": True, "response": "A complete answer."},
        build_question_contract(query),
    )
    assert envelope["doorway"]["prohibited_by_question_contract"] is True


def test_answer_envelope_is_attached_by_the_shared_response_floor_for_each_source():
    query = "What is photosynthesis?"
    for source in ("llm", "deterministic_fallback", "specialist", "exact_gold_star"):
        result = evaluate_response_floor(
            query,
            {
                "ok": True,
                "query": query,
                "response": "Photosynthesis converts light energy into chemical energy.",
                "response_provenance": {"class": source},
            },
            exact_standard=(source == "exact_gold_star"),
        )
        assert result["status"] == "pass"
        assert result["answer_envelope_validation"]["valid"] is True
        assert result["answer_envelope"]["state"] == "completed_answer"
        assert result["answer_envelope"]["governance"]["exact_standard_immutable"] is (
            source == "exact_gold_star"
        )


def test_envelope_validator_rejects_unknown_versions_and_missing_sections():
    assert validate_answer_envelope({"version": VERSION})["valid"] is False
    envelope = build_answer_envelope(
        "Question?", {"ok": True, "response": "Answer."},
        build_question_contract("Question?"),
    )
    wrong = dict(envelope, version="99.0")
    assert validate_answer_envelope(wrong)["reason"] == "unsupported_version"



def test_answer_envelope_uses_route_owned_capability_declaration():
    query = "Explain a concept."
    payload = {
        "ok": True,
        "response": "A bounded explanation.",
        "route_source": "guide_broad_conceptual_boundary",
    }
    envelope = build_answer_envelope(query, payload, build_question_contract(query))
    capability = envelope["capability"]
    assert capability["declaration_status"] == "declared"
    assert capability["registry_version"] == "1.0"
    assert capability["supported_task_families"] == ["bounded_conceptual_definition"]
    assert capability["semantic_competence_certified"] is False



def test_specialist_capability_is_recorded_separately_from_route_capability():
    query = "How can Philippine systems reinforce one another?"
    payload = {
        "ok": True,
        "response": "This is a bounded systems orientation.",
        "route_source": "deterministic-systems-preparation-entry",
        "systems_delegation": {
            "specialist_id": "systems_ph",
            "state": "available",
        },
    }
    envelope = build_answer_envelope(query, payload, build_question_contract(query))
    assert envelope["capability"]["declaration_status"] == "declared"
    assert envelope["specialist"]["id"] == "systems_ph"
    assert envelope["specialist"]["declaration_status"] == "declared"
    assert envelope["specialist"]["semantic_competence_certified"] is False


def test_answer_without_specialist_contribution_does_not_infer_specialist():
    envelope = build_answer_envelope(
        "What is photosynthesis?",
        {"ok": True, "response": "A concise explanation.", "route_source": "guide_basic_inquiry"},
        build_question_contract("What is photosynthesis?"),
    )
    assert envelope["specialist"]["id"] == "not_declared"
    assert envelope["specialist"]["declaration_status"] == "not_declared"
