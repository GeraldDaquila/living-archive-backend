"""Regression for answer-first Basic Inquiry stewardship comparisons."""

import main

QUESTION = (
    "A visitor asks how stewardship differs from management and ownership. "
    "What comparison structure would make the distinctions usable?"
)


def test_basic_inquiry_deterministic_recovery_answers_before_navigating():
    result = main._basic_inquiry_round1_deterministic_response(
        QUESTION,
        {},
        {"context_blocks": ""},
        recommendation_available=False,
    )
    paragraphs = result["response"].split("\n\n")
    assert len(paragraphs) == 3
    assert paragraphs[0].startswith("Ownership concerns the rights and claims")
    assert "management is the work" in paragraphs[0]
    assert "stewardship is responsibility" in paragraphs[0]
    assert "source of authority" in paragraphs[2]
    assert "time horizon" in paragraphs[2]
    assert result["provider"] == "gold_standard_registry_deterministic_fallback"
