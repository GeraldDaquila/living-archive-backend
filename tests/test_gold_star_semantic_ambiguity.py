"""Regression tests for semantic disambiguation and adaptive Gold Star composition."""

from general_guide_gold_standards import resolve_exact_gold_standard
from gold_star_lessons import active_quality_contribution, select_lesson
from general_guide_composition import _GENERAL_GUIDE_SYSTEM, _GENERAL_GUIDE_SYSTEM_COMPACT

QUESTION = (
    "Two sources use the same term differently. "
    "How should the Guide detect and explain the ambiguity before answering?"
)
BENCHMARK_ID = (
    "general-guide-semantic-ambiguity-same-term-different-sources-gold-star-2026-11-18"
)


def test_semantic_ambiguity_gold_star_is_exactly_resolvable_with_doorway():
    standard = resolve_exact_gold_standard(QUESTION)
    assert standard is not None
    assert standard["benchmark_id"] == BENCHMARK_ID
    assert "shared meaning" in standard["expected_response"].lower()
    assert "referent" in standard["expected_response"].lower()
    assert "genuine contradiction" in standard["expected_response"].lower()
    assert "ask one focused clarifying question" in standard["expected_response"].lower()
    assert standard["doorway_title"] == (
        "The Living Archive Navigator: Volume III – Knowledge & Sensemaking"
    )
    assert standard["doorway_url"].endswith("/the-living-archive-navigator-volume-iii/")
    assert standard["doorway_rationale"]


def test_semantic_ambiguity_lesson_contributes_only_its_reasoning_discipline():
    selected = select_lesson(QUESTION)
    assert selected is not None
    assert selected["benchmark_id"] == BENCHMARK_ID
    assert selected["exact"] is True

    contribution = active_quality_contribution(QUESTION)
    assert contribution is not None
    assert contribution["benchmark_id"] == BENCHMARK_ID
    assert contribution["authority_mode"] == "structural_guidance_only"
    assert "compare" in contribution["discipline"].lower()
    assert "contradiction" in contribution["discipline"].lower()
    assert "expected_response" not in contribution
    assert "doorway" not in contribution


def test_unrelated_decision_question_does_not_receive_semantic_ambiguity_lesson():
    selected = select_lesson("How should I decide whether to move to another city?")
    assert selected is None or selected["benchmark_id"] != BENCHMARK_ID


def test_compact_composition_contract_is_question_first_and_subject_adaptive():
    prompt = _GENERAL_GUIDE_SYSTEM_COMPACT
    assert "QUESTION-FIRST, SUBJECT-ADAPTIVE COMPOSITION CONTRACT" in prompt
    assert "delivery-quality floor, not a universal content template" in prompt
    assert "Treat every specialized section below as conditional" in prompt
    assert "SEMANTIC AMBIGUITY BEFORE ANSWERING" in prompt
    assert "Do not replace this task with generic decision, stewardship, or governance advice." in prompt
    assert "QUESTION-FIRST, SUBJECT-ADAPTIVE COMPOSITION CONTRACT" in _GENERAL_GUIDE_SYSTEM
    assert "SEMANTIC AMBIGUITY BEFORE ANSWERING" in _GENERAL_GUIDE_SYSTEM
