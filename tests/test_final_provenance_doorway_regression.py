import main

def test_provenance_boundary_does_not_promote_leading_unrelated_recovery(monkeypatch):
    query = "How does the Archive distinguish tools from the purposes they serve?"
    docs = [{
        "title": "Anchoring GESARA in Daily Life: Practical Tools for Embracing Financial Sovereignty",
        "url": "https://geralddaquila.com/example/financial-sovereignty/",
        "text": "Financial sovereignty and daily life.",
    }]
    monkeypatch.setattr(main, "_parse_context_documents", lambda context: docs)
    monkeypatch.setattr(main, "_canonical_primary_from_docs", lambda docs, query, profile: None)
    result = main._boundary_canonical_doorway({"canonical_link_context": "nonempty"}, query)
    assert result is None
