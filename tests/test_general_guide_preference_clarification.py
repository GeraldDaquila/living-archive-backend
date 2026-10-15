"""Regression tests for preference-only General Guide input."""

from general_guide_composition import (
    _is_response_preference_without_subject,
    compose,
)


def test_preference_only_input_clarifies_instead_of_failing_retrieval():
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


def test_substantive_history_suppresses_preference_only_shortcut():
    assert not _is_response_preference_without_subject(
        "I want to understand the subject, not receive advice.",
        "I am asking about institutional responsibility in public governance.",
    )


def test_named_subject_request_is_not_preference_only():
    assert not _is_response_preference_without_subject(
        "I want to understand institutional responsibility, not receive advice.",
        "",
    )


def test_unrelated_incomplete_query_is_not_misclassified_as_preference():
    assert not _is_response_preference_without_subject(
        "I want to understand the subject.",
        "",
    )
