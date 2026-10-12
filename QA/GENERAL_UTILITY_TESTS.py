"""Contract tests for the USE General Utility candidate."""
from __future__ import annotations

from general_utility import build_contribution, inquiry_shape


DOCS = [
    {
        "title": "Example Concept",
        "url": "https://geralddaquila.com/example-concept/",
        "text": "Attention is a human capacity shaped by context. It relates to how people direct presence toward what matters.",
    },
    {
        "title": "Example Relationship",
        "url": "https://geralddaquila.com/example-relationship/",
        "text": "Relationships are shaped by patterns of attention, meaning, and response. These patterns can become visible through reflection.",
    },
]


def test_open_query_is_not_misclassified_as_specialist():
    assert inquiry_shape("How do people find meaning when the old way no longer works?")["mode"] == "open_inquiry"


def test_conceptual_query_constructs_from_supplied_evidence():
    result = build_contribution("What is attention?", DOCS, route_authorized=True)
    assert result.status == "READY"
    assert result.mode == "conceptual"
    assert "Example Concept" in result.answer
    assert result.canonical_candidates


def test_lived_query_preserves_sovereignty():
    result = build_contribution(
        "I feel lost after a major change and do not know what it means.",
        DOCS,
        route_authorized=True,
    )
    assert result.status == "READY"
    assert result.mode == "lived_experience"
    assert "you should" not in result.answer.casefold()
    assert "must" not in result.answer.casefold()


def test_no_evidence_is_not_fabricated():
    result = build_contribution("What is attention?", [], route_authorized=True)
    assert result.status == "NEEDS_RETRY"
    assert result.answer == ""


def test_utility_requires_use_authorization():
    result = build_contribution("What is attention?", DOCS, route_authorized=False)
    assert result.status == "NOT_AUTHORIZED"


def test_risk_is_delegated():
    result = build_contribution("I want to end my life.", DOCS, route_authorized=True)
    assert result.status == "DELEGATE"
    assert result.mode == "risk"
