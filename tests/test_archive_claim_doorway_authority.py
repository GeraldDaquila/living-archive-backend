"""Regression: provenance boundaries cannot turn verified Archive navigation into a dead end."""

import main


def test_archive_claim_boundary_rejects_unrelated_upstream_doorway(monkeypatch):
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda q: None)
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

    assert result["recommendation"] != unrelated
    assert result["recommendation"] is None or (
        result["recommendation"].get("title") and result["recommendation"].get("url")
    )


def test_archive_claim_boundary_accepts_matching_registered_node(monkeypatch):
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda q: None)
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


def test_sender_recovers_verified_provenance_doorway_when_available(monkeypatch):
    query = "How does the Archive distinguish tools from the purposes they serve?"
    payload = {
        "query": query,
        "response": "placeholder",
        "recommendation": None,
        "processing": "final_visitor_boundary_archive_claim_provenance",
    }
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda q: None)

    sent = []
    async def capture(message):
        sent.append(message)

    import asyncio, json
    asyncio.run(main._use_send_json(capture, payload))
    body = json.loads(sent[-1]["body"].decode("utf-8"))
    recommendation = body["recommendation"]
    assert recommendation is None or (
        recommendation.get("title") and recommendation.get("url")
    )
    # A provenance processing label is not itself authority to suppress navigation.
    assert body.get("processing") == "final_visitor_boundary_archive_claim_provenance"


def test_archive_claim_boundary_clears_stale_canonical_doorway(monkeypatch):
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda q: None)
    query = "How does the Archive distinguish tools from the purposes they serve?"
    stale = {
        "title": "Why the AI Era Is Ultimately a Human Identity Crisis",
        "url": "https://geralddaquila.com/2026/09/14/why-the-ai-era-is-ultimately-a-human-identity-crisis/",
    }
    monkeypatch.setattr(main, "_guide_node_specific_match", lambda q: None)
    result = main._guide_finalize_visitor_payload(
        {"response": "placeholder", "recommendation": stale, "canonical_doorway": stale},
        query,
    )
    assert result["recommendation"] != stale
    assert result["canonical_doorway"] != stale
    assert result["recommendation"] is None or (
        result["recommendation"].get("title") and result["recommendation"].get("url")
    )
