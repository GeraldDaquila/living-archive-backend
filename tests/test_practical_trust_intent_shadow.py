"""Shadow calibration for practical-application intent and response shape.

The observed trust question is preserved as a regression probe. These tests
exercise only a diagnostic module and do not alter live Guide behavior.
"""
from guide_practical_intent_shadow import (
    classify_practical_application_intent,
    has_observable_organizational_practice,
)


TRUST_QUESTION = (
    "I understand the importance of trust, but what would I actually do "
    "differently in an organization trying to live by it?"
)

GENERIC_INQUIRY_RESPONSE = (
    "Separate what is known from what is inferred, then ask which distinction "
    "or tension matters most. Notice what is observable, what depends on "
    "interpretation, and what missing fact could change the picture."
)

PRACTICAL_TRUST_RESPONSE = (
    "Make commitments visible by agreeing who owns each action and when it is due, "
    "then close the loop when it is complete. Explain the reasons behind decisions, "
    "make it safe to raise concerns without punishment, and have leaders acknowledge "
    "their mistakes and follow through on repairs when trust is damaged."
)


def test_observed_trust_question_is_practical_application_not_conceptual():
    assert classify_practical_application_intent(TRUST_QUESTION) == "practical_application"


def test_practical_application_paraphrases_are_recognized_without_topic_specific_routing():
    probes = (
        "How would we put fairness into practice in a team?",
        "What would our organization actually do differently to honor accountability?",
        "What does a culture of trust look like day to day?",
        "How can a group live by this principle in practice?",
    )
    assert all(
        classify_practical_application_intent(query) == "practical_application"
        for query in probes
    )


def test_conceptual_questions_are_not_overclassified_as_practical():
    probes = (
        "Why does trust matter in an organization?",
        "What does trust mean?",
        "Define organizational trust.",
    )
    assert all(classify_practical_application_intent(query) == "conceptual" for query in probes)


def test_observed_generic_inquiry_answer_does_not_satisfy_practical_contract():
    assert not has_observable_organizational_practice(GENERIC_INQUIRY_RESPONSE)


def test_concrete_trust_answer_demonstrates_observable_practices():
    assert has_observable_organizational_practice(PRACTICAL_TRUST_RESPONSE)
