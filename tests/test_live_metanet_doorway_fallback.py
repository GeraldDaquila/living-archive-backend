import main

def test_retrieval_boundary_does_not_promote_leading_unrelated_asset(monkeypatch):
    query = "How does the Archive distinguish tools from the purposes they serve?"
    docs = [{
        "title": "Anchoring GESARA in Daily Life: Practical Tools for Embracing Financial Sovereignty",
        "url": "https://geralddaquila.com/example/financial-sovereignty/",
        "text": "Financial sovereignty and daily life.",
    }]
    monkeypatch.setattr(main, "_general_guide_authoritative_doorway", lambda q, data: None)
    monkeypatch.setattr(main, "_parse_context_documents", lambda _: docs)
    data = {"canonical_link_context": "nonempty"}
    result = main._recommendation_first_fetch.__wrapped__ if hasattr(main._recommendation_first_fetch, "__wrapped__") else None
    assert main._general_guide_authoritative_doorway(query, data) is None
