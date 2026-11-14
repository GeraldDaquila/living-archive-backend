"""Regression contract for bounded conceptual orientation after evidence miss."""

import main


def test_recognized_concept_gets_useful_bounded_orientation_without_archive_claim():
    result = main._basic_inquiry_round1_deterministic_response(
        "What is spiritual bypassing, and why does it matter?",
        {},
        {},
    )
    response = result["response"].lower()
    assert "using spiritual beliefs" in response
    assert "difficult emotions" in response
    assert "spirituality itself is not a problem" in response
    assert "archive material" in response
    assert result["recommendation"] is None


def test_unrecognized_question_keeps_generic_bounded_orientation():
    result = main._basic_inquiry_round1_deterministic_response(
        "What is the zyxw concept, and why does it matter?",
        {},
        {},
    )
    response = result["response"].lower()
    assert "central tension visible" in response
    assert "using spiritual beliefs" not in response
    assert result["recommendation"] is None
