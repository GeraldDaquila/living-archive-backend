"""Regression tests for Guide resource-language / recommendation consistency."""

import main


def test_unavailable_recommendation_cannot_be_promised_in_visitor_text():
    response = (
        "Your question asks about a community archive. "
        "If you would like to explore this further, the Archive resource below "
        "may offer a useful next step."
    )

    result = main._guide_reconcile_resource_language(response, recommendation_available=False)

    assert "resource below" not in result.lower()
    assert "I could not identify a sufficiently relevant Archive resource to recommend here." in result


def test_unavailable_recommendation_does_not_duplicate_existing_boundary_sentence():
    response = (
        "The answer is based on general knowledge. "
        "The Archive resource below may offer a useful next step. "
        "I could not identify a sufficiently relevant Archive resource to recommend here."
    )

    result = main._guide_reconcile_resource_language(response, recommendation_available=False)

    assert "resource below" not in result.lower()
    assert result.count("I could not identify a sufficiently relevant Archive resource to recommend here.") == 1


def test_available_recommendation_preserves_proportionate_resource_language():
    response = "The Archive resource below may offer a useful next step."

    result = main._guide_reconcile_resource_language(response, recommendation_available=True)

    assert result == response


def test_unrelated_answer_is_not_rewritten_when_no_recommendation_exists():
    response = "Keep one reading list and review it once a week."

    result = main._guide_reconcile_resource_language(response, recommendation_available=False)

    assert result == response
