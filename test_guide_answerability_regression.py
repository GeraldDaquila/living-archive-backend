"""Regression tests for layered conceptual answerability."""

from guide_answerability import is_unjustified_conceptual_abstention


def test_plural_limits_question_catches_generic_evidence_abstention():
    query = "What are the limits of self-optimization as a model of development?"
    response = (
        "I can't define The limits of self-optimization as a model of development "
        "reliably from the information available in this response alone."
    )
    assert is_unjustified_conceptual_abstention(query, response)


def test_plural_limits_paraphrases_are_covered():
    cases = [
        ("What are the risks of optimizing a system around one metric?", "I cannot explain this reliably from the information available."),
        ("What are the boundaries of self-improvement?", "There is not enough information to answer reliably."),
        ("What are the trade-offs of continuous optimization?", "I can't determine the answer from this response alone."),
    ]
    for query, response in cases:
        assert is_unjustified_conceptual_abstention(query, response), query


def test_general_conceptual_question_still_catches_singular_form():
    assert is_unjustified_conceptual_abstention(
        "What is the purpose of feedback in organizational learning?",
        "I cannot explain the purpose reliably from the information available.",
    )


def test_source_only_and_high_stakes_requests_remain_excluded():
    refusal = "I cannot explain this reliably from the information available."
    assert not is_unjustified_conceptual_abstention(
        "What are the limits according to the Living Archive only?", refusal
    )
    assert not is_unjustified_conceptual_abstention(
        "What are the risks of this medication?", refusal
    )
    assert not is_unjustified_conceptual_abstention(
        "What are the legal limits of this contract?", refusal
    )


def test_unrelated_questions_do_not_trigger():
    assert not is_unjustified_conceptual_abstention(
        "What are the opening hours tomorrow?",
        "I cannot determine that reliably from the information available.",
    )
