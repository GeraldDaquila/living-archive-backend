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
        "What is the strongest alternative explanation?",
        "Does it recur under comparable conditions",
        "What plausible mechanism connects the observations",
        "What constraints or alternative explanations could produce the same result",
        "what specific observation would count against your interpretation",
        "five reports repeating one original claim are not five independent confirmations",
        "let resonance generate a hypothesis",
        "pause before irreversible action",
        "revise or release the interpretation",
    ):
        assert required.casefold() in answer.casefold()
    assert "not enough grounded material" not in answer.casefold()
    assert "organizational" not in answer.casefold()


def test_resonance_question_selects_the_directly_relevant_patterns_doorway():
    doorway = registered_recovery_recommendation(QUERY)
    assert doorway["title"] == "Seeing Patterns Without Fooling Yourself"
    assert doorway["url"] == (
        "https://geralddaquila.com/2026/04/06/seeing-patterns-without-fooling-yourself/"
    )
    assert "repeatability, mechanism, constraints, and disconfirmation" in doorway["rationale"]


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



def test_final_visitor_boundary_replaces_generic_answer_and_restores_verified_doorway():
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
    assert result["recommendation"]["title"] == "Seeing Patterns Without Fooling Yourself"
    assert result["canonical_doorway"] == result["recommendation"]
    assert result["doorway_title"] == "Seeing Patterns Without Fooling Yourself"
    assert result["doorway_url"] == (
        "https://geralddaquila.com/2026/04/06/seeing-patterns-without-fooling-yourself/"
    )
    assert result["doorway_rationale"]
    assert result["answer_basis"]["kind"] == "general_knowledge"
    assert result["processing"] == "final_visitor_boundary_resonance_confirmation_bias_recovery"


def test_final_visitor_boundary_does_not_capture_nearby_but_different_questions():
    import main

    query = "How can I recognize confirmation bias in a research project?"
    original = "A concise explanation of confirmation bias in research."
    result = main._guide_finalize_visitor_payload({"response": original}, query)
    assert result["response"] == original
