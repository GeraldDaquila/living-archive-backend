"""Focused acceptance tests for one-sided team-conflict reasoning."""
from pathlib import Path

import main

from one_sided_team_conflict_contract import (
    build_one_sided_team_conflict_instruction,
    evaluate_one_sided_team_conflict_response,
    is_one_sided_team_conflict_question,
    recover_one_sided_team_conflict_response,
)

TARGET = (
    "A visitor wants to apply an Archive idea to a team conflict but has provided "
    "only one person's account. What context should the Guide ask for before offering a frame?"
)


def test_target_question_activates_scoped_contract():
    assert is_one_sided_team_conflict_question(TARGET)
    assert "without treating one account as the complete record" in build_one_sided_team_conflict_instruction(TARGET)


def test_recovery_passes_all_required_context_checks():
    response = recover_one_sided_team_conflict_response()
    report = evaluate_one_sided_team_conflict_response(TARGET, response)
    assert report == {"applies": True, "passed": True, "missing": []}


def test_partial_account_does_not_mean_dismiss_the_visitor():
    response = recover_one_sided_team_conflict_response().casefold()
    assert "taking that person's experience seriously" in response
    assert "one person's account" in response


def test_safety_is_checked_before_recommending_dialogue():
    response = recover_one_sided_team_conflict_response().casefold()
    assert response.index("safe and appropriate") < response.index("before choosing a frame")
    assert "retaliation risk" in response
    assert "facilitated" in response


def test_unrelated_team_disagreement_does_not_trigger_contract():
    assert not is_one_sided_team_conflict_question(
        "How can our team resolve a disagreement about meeting schedules?"
    )


def test_non_team_personal_relationship_does_not_trigger_contract():
    assert not is_one_sided_team_conflict_question(
        "How should I understand a conflict with a close friend?"
    )


def test_prompt_and_parser_and_final_boundary_are_integrated():
    source = Path(__file__).with_name("general_guide_composition.py").read_text(encoding="utf-8")
    assert "build_one_sided_team_conflict_instruction(question)" in source
    assert "evaluate_one_sided_team_conflict_response(query, response)" in source
    assert "evaluate_one_sided_team_conflict_response(question, candidate)" in source
    assert "recover_one_sided_team_conflict_response()" in source


def test_irrelevant_retrieval_doorway_is_not_part_of_contract_response():
    response = recover_one_sided_team_conflict_response()
    assert "NESARA" not in response
    assert "GESARA" not in response


def test_verified_team_conflict_doorway_family_is_selected():
    assert main._select_verified_doorway_conceptual_family(TARGET) == "one_sided_team_conflict_context"


def test_irrelevant_upstream_doorway_is_replaced_at_terminal_restore():
    decoy = {
        "title": "What Is NESARA and GESARA? Origins, Claims, and Why the Theory Keeps Resurfacing",
        "url": "https://geralddaquila.com/2026/10/19/nesara-gesara-a-vision-for-global-financial-reform-amid-systemic-discontent/",
        "rationale": "Unrelated resource.",
    }
    result = main._guide_restore_verified_doorway(
        {"response": "A complete answer.", "recommendation": decoy}, TARGET
    )
    assert result["recommendation"]["title"] == "Building Trust-Centered Organizations"
    assert result["recommendation"]["url"] == "https://geralddaquila.com/2026/09/07/building-trust-centered-organizations/"
    assert result["doorway_selection_status"] == "VERIFIED_RELEVANT_DESTINATION"
    assert result["doorway_selection_source"] == "reviewed_one_sided_team_conflict_family"
