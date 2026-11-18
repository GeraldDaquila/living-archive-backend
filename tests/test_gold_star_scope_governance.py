"""Regression tests for Gold Star scope governance and cross-domain regression handling."""

from general_guide_gold_standards import resolve_exact_gold_standard
from gold_star_lessons import active_quality_contribution, select_lesson
from general_guide_composition import _GENERAL_GUIDE_SYSTEM, _GENERAL_GUIDE_SYSTEM_COMPACT

QUESTION = "A new Gold Star appears to improve responses in one domain but degrades responses in another. How should USE determine whether its scope should be narrowed, revised, or rejected?"
BENCHMARK_ID = "general-guide-gold-star-scope-governance-cross-domain-regression-2026-11-18"


def test_scope_governance_gold_star_is_exactly_resolvable_with_verified_doorway():
    standard = resolve_exact_gold_standard(QUESTION)
    assert standard is not None
    assert standard["benchmark_id"] == BENCHMARK_ID
    answer = standard["expected_response"].lower()
    assert "narrow the scope" in answer
    assert "revise when" in answer
    assert "reject when" in answer
    assert "unrelated negative controls" in answer
    assert "scope expands only after new evidence" in answer
    assert standard["doorway_title"] == "The Sovereign Sensemaking Compass"
    assert standard["doorway_url"].endswith("/the-sovereign-sensemaking-compass")
    assert standard["doorway_rationale"]


def test_scope_governance_lesson_is_exact_and_structural_only():
    selected = select_lesson(QUESTION)
    assert selected is not None
    assert selected["benchmark_id"] == BENCHMARK_ID
    assert selected["exact"] is True
    contribution = active_quality_contribution(QUESTION)
    assert contribution is not None
    assert contribution["benchmark_id"] == BENCHMARK_ID
    assert contribution["authority_mode"] == "structural_guidance_only"
    assert "narrow" in contribution["discipline"].lower()
    assert "regression" in contribution["discipline"].lower()
    assert "expected_response" not in contribution
    assert "doorway" not in contribution


def test_scope_governance_lesson_does_not_leak_into_unrelated_questions():
    for question in (
        "How can I improve my garden soil?",
        "What is the difference between weather and climate?",
        "How should a teacher explain fractions to a child?",
    ):
        selected = select_lesson(question)
        assert selected is None or selected["benchmark_id"] != BENCHMARK_ID


def test_scope_governance_prompt_is_explicitly_meta_governance_only():
    for prompt in (_GENERAL_GUIDE_SYSTEM, _GENERAL_GUIDE_SYSTEM_COMPACT):
        assert "GOLD STAR SCOPE GOVERNANCE (META-GOVERNANCE TASKS ONLY)" in prompt
        assert "never impose it on ordinary visitor questions" in prompt
        assert "unrelated negative controls" in prompt
