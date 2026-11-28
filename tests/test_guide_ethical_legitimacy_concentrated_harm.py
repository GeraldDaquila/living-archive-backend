"""Regression tests for ethical legitimacy when lawful popular policy concentrates harm."""

import json
from pathlib import Path

from deterministic_answer_recovery import compose_task_specific_recovery

ROOT = Path(__file__).resolve().parents[1]
QUERY = "A policy is legal and popular but may impose concentrated harm on a minority. How should the Guide frame the ethical question without pretending the Archive supplies a verdict?"


def test_concentrated_harm_question_gets_ethical_frame_before_boundary_analysis():
    result = compose_task_specific_recovery(QUERY)
    assert result is not None
    assert result["recovery_id"] == "task_ethical_legitimacy_concentrated_harm"
    answer = result["response"].casefold()
    for concept in (
        "legality tells us",
        "popularity tells us",
        "ethically defensible",
        "who receives",
        "who bears",
        "meaningful voice",
        "less harmful workable alternatives",
        "proportionality",
        "the archive can help",
        "should not be presented as having issued a verdict",
        "reasonable disagreement",
        "accountable for reviewing the harm",
    ):
        assert concept in answer


def test_trigger_handles_close_paraphrase():
    result = compose_task_specific_recovery(
        "When a lawful, widely supported policy places disproportionate costs on a small community, "
        "how can we assess its ethical legitimacy without claiming the Archive decides?"
    )
    assert result is not None
    assert result["recovery_id"] == "task_ethical_legitimacy_concentrated_harm"


def test_nonmatching_policy_questions_do_not_capture_the_contract():
    for query in (
        "What is the difference between a policy and a procedure?",
        "How should a policy be communicated to the public?",
        "What kinds of boundaries should be drawn around a problem, and what do they exclude?",
        "How can a popular policy be implemented efficiently?",
    ):
        result = compose_task_specific_recovery(query)
        assert not result or result["recovery_id"] != "task_ethical_legitimacy_concentrated_harm"


def test_original_boundary_answer_is_preserved_as_near_miss_not_gold_star():
    fixture = json.loads(
        (ROOT / "tests/fixtures/general_guide_policy_legality_minority_harm_nearmiss.json")
        .read_text(encoding="utf-8")
    )
    assert fixture["status"] == "NEAR_MISS"
    assert fixture["immutable"] is True
    assert fixture["gold_star_eligible"] is False
    assert "problem boundary" in fixture["original_response"].casefold()
    assert "task_ethical_legitimacy_concentrated_harm" not in fixture["original_response"]


def test_corrected_exemplar_is_separate_and_has_no_automatic_runtime_authority():
    fixture = json.loads(
        (ROOT / "tests/fixtures/general_guide_policy_legality_minority_harm_gold_star.json")
        .read_text(encoding="utf-8")
    )
    assert fixture["status"] == "USER_APPROVED_GOLD_STANDARD_CANDIDATE"
    assert fixture["explicit_user_elevation_approval"] is True
    assert fixture["query"] == QUERY
    assert fixture["expected_response"] == compose_task_specific_recovery(QUERY)["response"]
    assert fixture["runtime_transfer"] is False
    assert fixture["exact_answer_authority"] is False
    assert fixture["deterministic_fallback_eligible"] is False
