"""Two-level regression contract for orientation rather than information."""
import general_guide_composition as guide
from deterministic_answer_recovery import (
    compose_recovery,
    has_orientation_information_explanation,
    is_orientation_information_contrast_question,
)


QUESTION = "What does “orientation rather than information” mean in practice?"


def test_query_level_recognizes_the_original_question_and_paraphrases():
    assert is_orientation_information_contrast_question(QUESTION)
    assert is_orientation_information_contrast_question(
        "What is the difference between orientation and information?"
    )
    assert is_orientation_information_contrast_question(
        "Explain orientation instead of information in practice."
    )


def test_query_classifier_does_not_capture_unrelated_information_questions():
    assert not is_orientation_information_contrast_question(
        "Where can I find information about school attendance?"
    )
    assert not is_orientation_information_contrast_question(
        "How do I organize information for a report?"
    )


def test_deterministic_recovery_answers_the_contrast_with_a_practical_example():
    answer = compose_recovery(QUESTION)
    assert has_orientation_information_explanation(answer)
    assert "Information gives you facts" in answer
    assert "The scores are information" in answer
    assert "orientation depends on information" in answer.casefold()


def test_architectural_boundary_replaces_abstention_after_provider_composition():
    abstention = (
        "I can't define orientation rather than information reliably from the "
        "information available in this response alone. I don't want to invent a definition."
    )
    answer = guide.enforce_response_contracts(QUESTION, abstention)
    assert has_orientation_information_explanation(answer)
    assert "I can't define" not in answer


def test_architectural_boundary_preserves_a_valid_provider_explanation():
    valid = (
        "Information gives you facts and details. Orientation helps place that information "
        "in context, showing relationships and stakes so you can judge what matters and act. "
        "For example, test scores are information; understanding attendance and teaching "
        "conditions helps a school decide what response is appropriate."
    )
    assert guide.enforce_response_contracts(QUESTION, valid) == valid


def test_semantic_acceptance_rejects_keyword_stuffing_without_the_actual_distinction():
    superficial = (
        "Information and orientation involve facts, context, relationships, and judgment. "
        "For example, these ideas can be important."
    )
    assert not has_orientation_information_explanation(superficial)
