"""Regressions for intuitive resonance versus confirmation-bias discernment."""

from deterministic_answer_recovery import (
    _resonance_confirmation_bias_recovery,
    compose_recovery,
    has_registered_recovery,
    is_resonance_confirmation_bias_question,
    registered_recovery_recommendation,
)


QUERY = "Before acting on an intuitive impression, can I distinguish resonance from confirmation bias?"


def test_exact_resonance_question_is_classified_as_discernment_not_generic_reflection():
    assert is_resonance_confirmation_bias_question(QUERY)
    assert has_registered_recovery(QUERY)


def test_resonance_recovery_distinguishes_signal_from_evidence_and_bias():
    answer = compose_recovery(QUERY)
    assert answer == _resonance_confirmation_bias_recovery()
    for required in (
        "felt sense of recognition, coherence, or fit",
        "it is not proof that the idea is true",
        "what you directly observed",
        "the meaning you are assigning to it",
        "strongest alternative explanation",
        "what specific evidence would weaken your preferred reading",
        "apparently independent sources really are independent",
        "let resonance open an inquiry",
        "delay irreversible action",
        "revise the interpretation",
    ):
        assert required in answer
    assert "not enough grounded material" not in answer.casefold()
    assert "organizational" not in answer.casefold()


def test_resonance_question_does_not_force_an_unverified_archive_doorway():
    assert registered_recovery_recommendation(QUERY) is None


def test_resonance_classifier_has_narrow_negative_controls():
    for query in (
        "What is resonance in physics?",
        "What is confirmation bias?",
        "Why do intuitive impressions feel meaningful?",
        "How can I trust my intuition?",
        "What is the difference between resonance and dissonance?",
        "How can I recognize confirmation bias in a research project?",
    ):
        assert not is_resonance_confirmation_bias_question(query), query
