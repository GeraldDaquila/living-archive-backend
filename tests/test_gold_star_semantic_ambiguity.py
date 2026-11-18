"""Regression tests for semantic disambiguation and adaptive Gold Star composition."""

from general_guide_gold_standards import resolve_exact_gold_standard
from gold_star_lessons import active_quality_contribution, select_lesson
from general_guide_composition import (
    _GENERAL_GUIDE_SYSTEM,
    _GENERAL_GUIDE_SYSTEM_COMPACT,
    _has_conflicting_information_discernment,
    _has_archive_grounding_boundary,
)

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
    assert "sharing a meaning" in standard["expected_response"].lower()
    assert "refers to" in standard["expected_response"].lower()
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
    assert "QUESTION-FIRST, TASK-DEPENDENT COMPOSITION GOVERNANCE" in prompt
    assert "quality and reasoning-governance standard, not a prescribed answer template" in prompt
    assert "Do not impose a fixed paragraph count, three-move sequence, or prose format" in prompt
    assert "DEFAULT GOLD STAR STRUCTURAL TEMPLATE" not in prompt
    assert "three connected, readable paragraphs" not in prompt
    assert "Paragraphs are a readability tool, not a compliance target" in prompt
    assert "Specialized guidance is conditional" in prompt
    assert "QUESTION-FIRST, TASK-DEPENDENT COMPOSITION GOVERNANCE" in _GENERAL_GUIDE_SYSTEM
    assert "Do not impose a fixed paragraph count" in _GENERAL_GUIDE_SYSTEM
    assert "SEMANTIC AMBIGUITY BEFORE ANSWERING" in prompt
    assert "Do not replace this task with generic decision, stewardship, or governance advice." in prompt
    assert "QUESTION-FIRST, TASK-DEPENDENT COMPOSITION GOVERNANCE" in _GENERAL_GUIDE_SYSTEM
    assert "SEMANTIC AMBIGUITY BEFORE ANSWERING" in _GENERAL_GUIDE_SYSTEM


CALIBRATION_VALIDATION_QUESTION = (
    "A revised Guide performs better on the calibration set but worse on the validation set. "
    "Which result should govern the decision to promote the revision, and why?"
)
CALIBRATION_VALIDATION_BENCHMARK_ID = (
    "general-guide-calibration-vs-validation-promotion-decision-gold-star-2026-11-18"
)


def test_calibration_validation_gold_star_is_exact_and_question_specific():
    standard = resolve_exact_gold_standard(CALIBRATION_VALIDATION_QUESTION)
    assert standard is not None
    assert standard["benchmark_id"] == CALIBRATION_VALIDATION_BENCHMARK_ID
    answer = standard["expected_response"].lower()
    assert "validation result should govern promotion" in answer
    assert "should not be promoted" in answer
    assert "data leakage" in answer and "split integrity" in answer
    assert "reproducible improvement" in answer
    assert standard["doorway_title"] is None
    assert standard["doorway_url"] is None


def test_calibration_validation_gold_star_transfers_only_model_evaluation_discipline():
    selected = select_lesson(CALIBRATION_VALIDATION_QUESTION)
    assert selected is not None
    assert selected["benchmark_id"] == CALIBRATION_VALIDATION_BENCHMARK_ID
    contribution = active_quality_contribution(CALIBRATION_VALIDATION_QUESTION)
    assert contribution is not None
    assert contribution["benchmark_id"] == CALIBRATION_VALIDATION_BENCHMARK_ID
    assert contribution["authority_mode"] == "structural_guidance_only"
    assert "held-out validation" in contribution["discipline"].lower()
    assert "expected_response" not in contribution
    assert "doorway" not in contribution


def test_calibration_validation_lesson_does_not_capture_unrelated_decision_questions():
    selected = select_lesson("Should I promote a team member who exceeded one target but missed another?")
    assert selected is None or selected["benchmark_id"] != CALIBRATION_VALIDATION_BENCHMARK_ID


def test_full_and_compact_prompts_do_not_reimpose_a_universal_paragraph_template():
    for prompt in (_GENERAL_GUIDE_SYSTEM, _GENERAL_GUIDE_SYSTEM_COMPACT):
        assert "SYSTEM-WIDE GOLD STAR STRUCTURAL TEMPLATE" not in prompt
        assert "three purposeful paragraphs by default" not in prompt
        assert "defaults to three purposeful paragraphs" not in prompt
        assert "normally three purposeful, readable paragraphs" not in prompt
        assert "three-paragraph Guide Gold Standard" not in prompt
    assert "GOLD STAR QUALITY GOVERNANCE" in _GENERAL_GUIDE_SYSTEM
    assert "TASK-DEPENDENT PRESENTATION STANDARD" in _GENERAL_GUIDE_SYSTEM


def test_semantic_quality_validators_accept_task_complete_single_paragraph_responses():
    conflicting_information = (
        "Conflicting claims create a trust problem, not simply a shortage of information. "
        "Separate what is verified from what is inferred, compare source reliability and evidence, "
        "ask what evidence would change the conclusion, and act only when the evidence meets a threshold proportionate to the stakes."
    )
    assert _has_conflicting_information_discernment(conflicting_information)

    archive_boundary = (
        "Archive-grounded guidance should be traceable to published Living Archive material. "
        "General external knowledge can provide context but must not be presented as the Archive's "
        "position or doctrine. Preserving provenance lets visitors distinguish what the Archive "
        "supports from wider context and bounded synthesis."
    )
    assert _has_archive_grounding_boundary(archive_boundary)
