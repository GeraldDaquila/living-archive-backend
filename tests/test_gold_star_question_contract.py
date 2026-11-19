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


def test_explicit_no_handoff_and_no_web_constraints_are_captured():
    contract = build_question_contract(
        "Explain this without links or recommendations. Do not search the web."
    )
    assert contract["constraints"]["no_handoff"] is True
    assert contract["constraints"]["no_external_research"] is True
    assert contract["resolution"]["handoff"] == "prohibited"


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
