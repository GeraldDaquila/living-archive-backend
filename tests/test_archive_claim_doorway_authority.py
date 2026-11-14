"""Regression: provenance recovery cannot rerank visitor navigation."""

import main


def test_archive_claim_boundary_preserves_upstream_doorway(monkeypatch):
    query = "How does the Archive distinguish tools from the purposes they serve?"
    upstream = {
        "title": "USE: The Protection Layer",
        "url": "https://geralddaquila.com/",
    }

    def should_not_rerank(*args, **kwargs):
        raise AssertionError("final provenance boundary must not rerun doorway selection")

    monkeypatch.setattr(main, "_boundary_canonical_doorway", should_not_rerank)

    result = main._guide_finalize_visitor_payload(
        {"response": "placeholder", "recommendation": upstream},
        query,
    )

    assert result["recommendation"] == upstream


def test_archive_claim_boundary_rejects_unvalidated_upstream_doorway(monkeypatch):
    query = "How does the Archive distinguish tools from the purposes they serve?"
    monkeypatch.setattr(main, "_boundary_canonical_doorway", lambda *args, **kwargs: {
        "title": "Anchoring GESARA in Daily Life: Practical Tools for Embracing Financial Sovereignty",
        "url": "https://geralddaquila.com/example/financial-sovereignty/",
    })

    result = main._guide_finalize_visitor_payload(
        {"response": "placeholder", "recommendation": None},
        query,
    )

    assert result["recommendation"] is None
