"""Regression tests for practical-action responses to explicit how-to questions."""
from general_guide_composition import (
    _practical_application_recovery,
    has_observable_practical_actions,
    is_practical_application_question,
)


TRUST_QUESTION = (
    "I understand the importance of trust, but what would I actually do "
    "differently in an organization trying to live by it?"
)
GENERIC_RESPONSE = (
    "Separate what is known from what is inferred, then ask which distinction "
    "or tension matters most. What detail or context would make this concrete?"
)


def test_observed_trust_question_is_classified_as_practical():
    assert is_practical_application_question(TRUST_QUESTION)


def test_practical_paraphrases_are_classified_without_topic_specific_routing():
    for query in (
        "How would we put fairness into practice in a team?",
        "What would our organization actually do differently to honor accountability?",
        "What does a culture of trust look like day to day?",
        "How can a group live by this principle?",
    ):
        assert is_practical_application_question(query)


def test_conceptual_questions_are_not_overclassified():
    for query in (
        "Why does trust matter in an organization?",
        "What does trust mean?",
        "Define organizational trust.",
    ):
        assert not is_practical_application_question(query)


def test_generic_reflection_does_not_satisfy_practical_contract():
    assert not has_observable_practical_actions(GENERIC_RESPONSE)


def test_deterministic_recovery_contains_observable_actions_and_focused_question():
    response = _practical_application_recovery()
    assert has_observable_practical_actions(response)
    assert "Ask the people affected" in response
    assert "explain the reasons" in response
    assert "who is responsible" in response
    assert response.endswith("?")
