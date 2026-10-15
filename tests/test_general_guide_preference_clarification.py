"""Regression tests for General Guide response-style preferences."""

from general_guide_composition import (
    _has_response_style_preference,
    _is_response_preference_without_subject,
    clarification_response,
    compose,
)


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
