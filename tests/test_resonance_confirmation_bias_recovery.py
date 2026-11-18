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



def test_final_visitor_boundary_replaces_generic_provider_answer_and_preserves_no_doorway():
    import main

    result = main._guide_finalize_visitor_payload(
        {
            "response": (
                "The question raises a real issue. Consider what is at stake, "
                "who is affected, and what would change if the situation were understood differently."
            ),
            "recommendation": {"title": "Unrelated resource", "url": "https://example.com/unrelated"},
        },
        QUERY,
    )
    assert result["response"] == _resonance_confirmation_bias_recovery()
    assert result["answer"] == result["response"] if "answer" in result else True
    assert result["recommendation"] is None
    assert result["canonical_doorway"] is None
    assert result["doorway_title"] is None
    assert result["processing"] == "final_visitor_boundary_resonance_confirmation_bias_recovery"


def test_final_visitor_boundary_does_not_capture_nearby_but_different_questions():
    import main

    query = "How can I recognize confirmation bias in a research project?"
    original = "A concise explanation of confirmation bias in research."
    result = main._guide_finalize_visitor_payload({"response": original}, query)
    assert result["response"] == original
