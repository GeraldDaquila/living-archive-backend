"""Tests for the shared Gold Star v2 question contract."""
from gold_star_question_contract import (
    VERSION,
    build_question_contract,
    validate_question_contract,
)


def test_contract_is_versioned_and_preserves_unknowns_instead_of_guessing():
    contract = build_question_contract("Tell me something useful.")
    assert contract["version"] == VERSION
    assert contract["task"]["primary"] == "unresolved"
    assert contract["task"]["candidate_source"] == "none"
    assert contract["domain"]["primary"] == "unknown"
    assert contract["stakes"]["level"] == "unknown"
    assert contract["uncertainty"]["classification_confidence"] == "not_scored"
    assert validate_question_contract(contract)["valid"] is True


def test_mixed_intent_is_preserved_as_candidate_not_forced_into_single_class():
    contract = build_question_contract(
        "Explain the policy, and then compare it with our current procedure."
    )
    assert contract["state"] == "multi_intent_candidate"
    assert contract["task"]["semantic_resolution"] == "required"
    assert contract["task"]["primary"] == "unresolved"
    assert contract["task"]["candidate_source"] == "conservative_surface_signal"
    assert contract["uncertainty"]["task_candidate_confidence"] == "not_semantically_certified"


def test_explicit_no_handoff_and_no_web_constraints_are_captured():
    contract = build_question_contract(
        "Explain this without links or recommendations. Do not search the web."
    )
    assert contract["constraints"]["no_handoff"] is True
    assert contract["constraints"]["no_external_research"] is True
    assert contract["resolution"]["handoff"] == "prohibited"
    assert contract["constraints"]["no_followup"] is True
    assert contract["resolution"]["followup"] == "prohibited"


def test_question_contract_does_not_claim_semantic_confidence_or_completion():
    contract = build_question_contract("What caused the change?")
    assert contract["requested_outcome"] == "unresolved"
    assert contract["reasoning_mode"] == "unresolved"
    assert contract["evidence"]["standard"] == "route_to_determine"
    assert contract["uncertainty"]["classification_confidence"] == "not_scored"


def test_empty_query_is_a_valid_unknown_contract():
    contract = build_question_contract("")
    assert contract["state"] == "unknown"
    assert contract["task"]["primary"] == "unresolved"


def test_schema_validator_rejects_missing_fields_and_wrong_versions():
    contract = build_question_contract("What is stewardship?")
    assert validate_question_contract({"version": VERSION})["valid"] is False
    wrong = dict(contract, version="99.0")
    assert validate_question_contract(wrong)["reason"] == "unsupported_version"


def test_composer_and_shared_response_floor_consume_the_contract():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    composer = (root / "general_guide_composition.py").read_text(encoding="utf-8")
    floor = (root / "gold_star_response_floor.py").read_text(encoding="utf-8")
    assert "build_question_contract" in composer
    assert "QUESTION CONTRACT (conservative machine-readable planning input)" in composer
    assert "build_question_contract" in floor
    assert "question_contract" in floor



def test_personal_reference_is_a_retrieval_task_not_an_unfamiliar_definition():
    contract = build_question_contract(
        "What is my protocol when a teaching conflicts with my conscience, lived experience, or care for others?"
    )
    assert contract["personal_reference"]["detected"] is True
    assert contract["personal_reference"]["resolution"] == "retrieve_and_verify_before_answering"
    assert contract["requested_outcome"] == "recover_existing_personal_reference"
    assert contract["personal_reference"]["absence_claim_boundary"] == "not_found_in_available_context_only"


def test_personal_reference_detection_covers_prior_agreements_but_not_generic_concepts():
    assert build_question_contract("What did we agree about the framework?")["personal_reference"]["detected"]
    assert build_question_contract("What is a teaching protocol?")["personal_reference"]["detected"] is False


def test_deterministic_definition_fallback_does_not_turn_personal_reference_into_dictionary_advice():
    from deterministic_answer_recovery import compose_definition_significance

    answer = compose_definition_significance(
        "my protocol when a teaching conflicts with my conscience, lived experience, or care for others"
    )
    assert "I can help recover your protocol" in answer
    assert "dictionary" not in answer.casefold()
    assert "I won't replace your established position with a protocol I invent" in answer


def test_composer_has_explicit_personal_reference_retrieval_instructions():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "general_guide_composition.py").read_text(encoding="utf-8")
    assert "PERSONAL-REFERENCE RESOLUTION" in source
    assert "Do not infer that a personal protocol exists" in source



def test_personal_reference_contract_is_exposed_to_the_shared_response_floor():
    from gold_star_response_floor import evaluate_response_floor

    query = "What is my protocol when a teaching conflicts with my conscience?"
    result = evaluate_response_floor(
        query,
        {"ok": True, "query": query, "response": "A protocol is a set of rules."},
    )
    assert result["personal_reference_resolution"]["detected"] is True
    assert result["personal_reference_resolution"]["resolution"] == "retrieve_and_verify_before_answering"



def test_teaching_conflict_personal_reference_receives_specific_retrieval_route_candidate():
    contract = build_question_contract(
        "What is my protocol when a teaching conflicts with my conscience, lived experience, or care for others?"
    )
    assert contract["personal_reference"]["route_candidate"] == "teaching_conflict_discernment"
    assert contract["personal_reference"]["resolution"] == "retrieve_and_verify_before_answering"


def test_personal_stewardship_invitation_is_reflective_inquiry_not_definition_candidate():
    contract = build_question_contract(
        "Who or what is asking for responsible care through me?"
    )
    assert contract["task"]["primary"] == "reflective_inquiry_candidate"
    assert contract["task"]["semantic_resolution"] == "required"
    assert contract["task"]["candidate_source"] == "conservative_surface_signal"
    assert contract["domain"]["primary"] == "unknown"
    assert contract["uncertainty"]["classification_confidence"] == "not_scored"
