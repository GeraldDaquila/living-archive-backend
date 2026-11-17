"""Regression tests for reflective-conceptual questions in the Guide's General Use module."""

from general_guide_composition import (
    _GENERAL_GUIDE_SYSTEM,
    _GENERAL_GUIDE_SYSTEM_COMPACT,
    _question_shape,
    is_practical_application_question,
)


def test_abstract_how_can_question_remains_explanatory_not_a_how_to_request():
    question = "How can hope be disciplined without becoming cynical?"
    assert _question_shape(question) == "explanatory"
    assert not is_practical_application_question(question)


def test_reflective_conceptual_contract_requires_explanation_before_action():
    for prompt in (_GENERAL_GUIDE_SYSTEM_COMPACT, _GENERAL_GUIDE_SYSTEM):
        assert "answer the conceptual tension before offering any action" in prompt
        assert "Do not convert the question into a generic decision checklist" in prompt
        assert "Keep the explanation anchored to the named subject throughout all paragraphs" in prompt
        assert "Do not introduce adjacent topics, specialist tools, AI governance, or institutional accountability" in prompt


def test_explicit_practical_application_questions_remain_practical():
    assert is_practical_application_question(
        "What would our organization actually do differently to practice trust?"
    )
