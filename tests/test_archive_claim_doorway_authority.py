"""Regression: provenance recovery cannot rerank visitor navigation."""

import main


def test_archive_claim_boundary_preserves_valid_upstream_doorway(monkeypatch):
    query = "How does the Archive distinguish tools from the purposes they serve?"
    upstream = {
        "title": "Canonical Archive Resource",
        "url": "https://geralddaquila.com/canonical-resource/",
    }

    def should_not_rerank(*args, **kwargs):
        raise AssertionError("final provenance boundary must not rerun doorway selection")

    monkeypatch.setattr(main, "_boundary_canonical_doorway", should_not_rerank)

    result = main._guide_finalize_visitor_payload(
        {"response": "placeholder", "recommendation": upstream},
        query,
    )

    assert result["recommendation"] == upstream


def test_archive_claim_boundary_fails_closed_without_upstream_doorway(monkeypatch):
    query = "How does the Archive distinguish tools from the purposes they serve?"

    def should_not_rerank(*args, **kwargs):
        raise AssertionError("archive-claim boundary must fail closed, not retrieve a new doorway")

    monkeypatch.setattr(main, "_boundary_canonical_doorway", should_not_rerank)

    result = main._guide_finalize_visitor_payload(
        {"response": "placeholder", "recommendation": None},
        query,
    )

    assert result["recommendation"] is None
