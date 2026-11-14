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


def test_archive_claim_boundary_rejects_unrelated_upstream_doorway(monkeypatch):
    query = "How does the Archive distinguish tools from the purposes they serve?"
    unrelated = {
        "title": "Why the AI Era Is Ultimately a Human Identity Crisis",
        "url": "https://geralddaquila.com/example/ai-identity-crisis/",
    }
    monkeypatch.setattr(main, "_guide_node_specific_match", lambda q: None)

    result = main._guide_finalize_visitor_payload(
        {"response": "placeholder", "recommendation": unrelated},
        query,
    )

    assert result["recommendation"] is None


def test_archive_claim_boundary_accepts_matching_registered_node(monkeypatch):
    query = "How does the Archive distinguish tools from the purposes they serve?"
    canonical = {
        "title": "USE: The Protection Layer",
        "url": "https://geralddaquila.com/use-the-protection-layer/",
    }
    monkeypatch.setattr(main, "_guide_node_specific_match", lambda q: dict(canonical))

    result = main._guide_finalize_visitor_payload(
        {"response": "placeholder", "recommendation": dict(canonical)},
        query,
    )

    assert result["recommendation"] == canonical
