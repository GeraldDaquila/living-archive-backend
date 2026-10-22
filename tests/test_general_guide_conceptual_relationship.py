"""Regression tests for conceptual relationship questions in The Guide."""
from general_guide_composition import (
    _conceptual_relationship_recovery,
    has_conceptual_relationship_explanation,
    is_conceptual_relationship_question,
)


RELATIONSHIP_QUESTION = (
    "How might accountability, trust, and the ability to repair harm "
    "reinforce one another?"
)
GENERIC_PRACTICAL_RESPONSE = (
    "A practical way to approach this is to define the outcome you want, "
    "identify the main constraint, and choose one step small enough to test. "
    "Before acting, consider who else is affected and what could go wrong. "
    "Check the result against the original goal and adjust rather than assuming "
    "the first attempt must be final. What detail or context would make this "
    "question most concrete for you?"
)


def test_accountability_trust_harm_question_is_classified_as_conceptual_relationship():
    assert is_conceptual_relationship_question(RELATIONSHIP_QUESTION)


def test_conceptual_relationship_paraphrases_are_classified():
    for query in (
        "How do accountability and trust strengthen each other?",
        "What is the relationship between repairing harm and rebuilding trust?",
        "How can responsibility and repair support one another?",
    ):
        assert is_conceptual_relationship_question(query)


def test_generic_problem_solving_response_fails_relationship_contract():
    assert not has_conceptual_relationship_explanation(GENERIC_PRACTICAL_RESPONSE)


def test_recovery_explains_the_mechanism_between_concepts():
    response = _conceptual_relationship_recovery()
    assert has_conceptual_relationship_explanation(response)
    assert "because people can judge" in response
    assert "repair turns accountability into action" in response
    assert response.endswith("community?")


def test_conceptual_question_is_not_misclassified_as_practical_how_to():
    from general_guide_composition import is_practical_application_question

    assert not is_practical_application_question(RELATIONSHIP_QUESTION)
