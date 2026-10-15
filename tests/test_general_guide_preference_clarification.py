"""Regression tests for preference-only General Guide input."""

from general_guide_composition import compose


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


def test_preference_only_input_does_not_override_subject_in_history():
    result = compose(
        use_core=object(),
        query="I want to understand the subject, not receive advice.",
        context_data={},
        history_text="I am asking about institutional responsibility in public governance.",
    )

    # A substantive prior turn should leave normal composition in control.
    # The fake use_core cannot compose; this test checks that the narrow
    # preference-only shortcut did not return a clarification.
    assert result is None


def test_named_subject_request_is_not_preference_only():
    result = compose(
        use_core=object(),
        query="I want to understand institutional responsibility, not receive advice.",
        context_data={},
        history_text="",
    )

    assert result is None
