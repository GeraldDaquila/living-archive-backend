"""Regression tests for General Guide response-style preferences."""

from general_guide_composition import (
    _has_response_style_preference,
    _is_response_preference_without_subject,
    clarification_response,
    compose,
    correction_subject,
    is_exact_source_request,
    source_trace_has_prior_claim,
)


def test_exact_source_request_is_recognized():
    assert is_exact_source_request("Give me the exact source for that claim.")
    assert is_exact_source_request("Can you provide the original citation?")
    assert not is_exact_source_request("Explain institutional responsibility.")


def test_source_trace_without_prior_claim_is_clarified_before_retrieval():
    result = clarification_response("Give me the exact source for that claim.", "")
    assert result is not None
    assert result["clarification_reason"] == "source_claim_missing"
    assert "Please paste the claim" in result["response"]


def test_source_trace_without_prior_claim_asks_for_claim_and_suppresses_doorway():
    result = compose(
        use_core=object(),
        query="Give me the exact source for that claim.",
        context_data={},
        history_text="",
    )
    assert result is not None
    assert result["clarification_reason"] == "source_claim_missing"
    assert "Please paste the claim" in result["response"]
    assert result["doorway_title"] == ""


def test_source_trace_requires_prior_assistant_claim_not_user_only_history():
    assert not source_trace_has_prior_claim("user: What is institutional responsibility?")
    assert source_trace_has_prior_claim("assistant: Institutional responsibility means an organization answers for its decisions.")


def test_correction_request_recovers_the_subject_the_visitor_says_was_missed():
    query = (
        "I asked about institutional responsibility, but you answered about "
        "personal growth. Can you correct that?"
    )
    assert correction_subject(query) == "institutional responsibility"


def test_correction_request_accepts_reverse_subject_order():
    assert correction_subject(
        "You answered about personal growth, but I asked about institutional responsibility. "
        "Please correct that."
    ) == "institutional responsibility"


def test_ordinary_question_is_not_misclassified_as_a_correction():
    assert correction_subject("Explain institutional responsibility in plain language.") == ""


def test_advice_preference_without_subject_clarifies_without_retrieval():
    result = compose(
        use_core=object(),
        query="I want to understand the subject, not receive advice.",
        context_data={},
        history_text="",
    )
    assert result is not None
    assert result["response_shape"] == "clarifying"
    assert result["clarification_reason"] == "response_preference_subject_missing"
    assert "rather than giving advice" in result["response"]
    assert "What subject would you like to understand?" in result["response"]
    assert result["doorway_title"] == ""


def test_plain_language_preference_without_subject_clarifies_without_retrieval():
    result = compose(
        use_core=object(),
        query="Can you answer this without using technical or academic language?",
        context_data={},
        history_text="",
    )
    assert result is not None
    assert result["response_shape"] == "clarifying"
    assert "clear, everyday language" in result["response"]
    assert "What would you like to understand?" in result["response"]
    assert result["doorway_title"] == ""


def test_plain_language_preference_clarifies_before_retrieval_and_suppresses_recommendation():
    result = clarification_response(
        "Can you answer this without using technical or academic language?",
        "",
    )
    assert result is not None
    assert result["clarification_reason"] == "response_preference_subject_missing"
    assert result["response"] == (
        "Of course. I’ll use clear, everyday language and avoid technical "
        "or academic terms. What would you like to understand?"
    )


def test_named_subject_style_request_is_not_a_preference_only_clarification():
    assert clarification_response(
        "Explain institutional responsibility without technical language.",
        "",
    ) is None


def test_style_preference_is_detected_for_a_named_subject():
    query = "Explain institutional responsibility without technical language."
    assert _has_response_style_preference(query)
    assert not _is_response_preference_without_subject(query)


def test_plain_language_preference_is_detected():
    assert _has_response_style_preference(
        "Can you answer this without using technical or academic language?"
    )
    assert _has_response_style_preference("Please use plain language.")


def test_substantive_history_suppresses_preference_only_shortcut():
    assert not _is_response_preference_without_subject(
        "I want to understand the subject, not receive advice.",
        "I am asking about institutional responsibility in public governance.",
    )


def test_named_subject_advice_request_is_not_preference_only():
    assert not _is_response_preference_without_subject(
        "I want to understand institutional responsibility, not receive advice.",
        "",
    )


def test_unrelated_incomplete_query_is_not_misclassified_as_preference():
    assert not _is_response_preference_without_subject(
        "I want to understand the subject.",
        "",
    )
