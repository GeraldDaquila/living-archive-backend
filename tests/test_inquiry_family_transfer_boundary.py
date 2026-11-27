"""Regression tests for hard inquiry-family boundaries in adaptive lesson transfer."""
from inquiry_family_transfer_contract import (
    classify_inquiry_family,
    lesson_transfer_compatibility,
)
from gold_star_lessons import select_lesson_candidates
from gold_star_question_contract import build_question_contract
from gold_star_semantic_contract import evaluate_semantic_contract
from gold_star_response_floor import evaluate_response_floor


PAIN_IDENTITY_QUESTION = (
    "How should a person hold pain without turning it into a total identity?"
)
OFF_TARGET_GOVERNANCE_ANSWER = (
    "Start by defining the outcome the change must achieve, the responsibilities "
    "that cannot be lost, and the people who will live with its consequences. "
    "Then compare realistic options against those requirements rather than "
    "assuming the proposed course is the only one. Examine what each option makes "
    "possible, what it may damage, who bears the costs, and what evidence would "
    "justify changing direction. Choose deliberately, make the reasoning and "
    "limits visible, and remain accountable for what follows."
)
ON_TARGET_REFLECTIVE_ANSWER = (
    "Pain can be part of a person's story without becoming the whole of who they are. "
    "Holding it means acknowledging what hurt and allowing it to matter, while also "
    "making room for relationships, values, interests, and hopes that remain part "
    "of the self. You do not have to deny the pain or turn it into your identity."
)


def test_pain_and_identity_question_is_classified_before_generic_how_should_task():
    result = classify_inquiry_family(PAIN_IDENTITY_QUESTION)
    assert result["family"] == "personal_lived_reflective"
    contract = build_question_contract(PAIN_IDENTITY_QUESTION)
    assert contract["inquiry_family"]["family"] == "personal_lived_reflective"
    assert contract["task"]["primary"] == "lived_reflective_inquiry_candidate"
    assert contract["response"]["shape"] == "reflective_explanation"


def test_institutional_governance_lesson_is_incompatible_with_lived_pain_question():
    lesson = {
        "reasoning_family": "governance_balance_constitutional_stability_participatory_legitimacy_adaptive_responsiveness"
    }
    decision = lesson_transfer_compatibility(PAIN_IDENTITY_QUESTION, lesson)
    assert decision["compatible"] is False
    assert decision["reason"] == "cross_family_transfer_blocked"


def test_live_selector_abstains_from_institutional_lessons_for_pain_and_identity_question():
    assert select_lesson_candidates(PAIN_IDENTITY_QUESTION) == []


def test_genuine_community_decision_question_keeps_its_governed_candidate_set():
    query = (
        "How should a community decide whether limits on individual freedom are "
        "justified by shared responsibilities?"
    )
    assert classify_inquiry_family(query)["family"] == "unknown"
    candidates = select_lesson_candidates(query)
    assert candidates
    assert any(
        item.get("match_basis") == "governed_community_tradeoff_policy"
        for item in candidates
    )


def test_semantic_contract_rejects_governance_substitution_and_accepts_lived_answer():
    bad = evaluate_semantic_contract(
        PAIN_IDENTITY_QUESTION, {"ok": True, "response": OFF_TARGET_GOVERNANCE_ANSWER}
    )
    assert bad["question_type"] == "lived_reflective_inquiry"
    assert bad["status"] == "fail"
    assert set(bad["hard_failures"]) == {
        "addresses_named_lived_experience",
        "preserves_experience_identity_distinction",
    }

    good = evaluate_semantic_contract(
        PAIN_IDENTITY_QUESTION, {"ok": True, "response": ON_TARGET_REFLECTIVE_ANSWER}
    )
    assert good["question_type"] == "lived_reflective_inquiry"
    assert good["status"] == "review_required"
    assert good["hard_failures"] == []


def test_final_response_floor_enforces_lived_reflective_task_fit():
    result = evaluate_response_floor(
        PAIN_IDENTITY_QUESTION,
        {"ok": True, "intent": "TOPICAL_INQUIRY", "response": OFF_TARGET_GOVERNANCE_ANSWER,
         "route_source": "general_guide_composition"},
    )
    assert result["status"] == "fail"
    assert result["semantic_enforcement"]["enforced"] is True
    assert result["semantic_enforcement"]["status"] == "fail"
    assert result["semantic_enforcement"]["question_type"] == "lived_reflective_inquiry"
