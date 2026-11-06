"""Regression tests for bounded Pinecone structural discovery egress."""

import use_core


def test_structural_collection_discovery_has_a_bounded_query_budget(monkeypatch):
    calls = []

    def fake_embedding(query, *args, **kwargs):
        calls.append(("embedding", query))
        return [0.1, 0.2, 0.3]

    def fake_query_index(vector, top_k):
        calls.append(("query", top_k))
        return []

    monkeypatch.setattr(use_core, "generate_embedding", fake_embedding)
    monkeypatch.setattr(use_core, "_query_index", fake_query_index)

    for collection_name, aliases in use_core.COLLECTION_TERMS.items():
        calls.clear()
        assert use_core._query_structural_index(collection_name) == []

        query_calls = [value for kind, value in calls if kind == "query"]
        embedding_calls = [value for kind, value in calls if kind == "embedding"]

        # Two intentionally distinct probes per alias: exact vocabulary and
        # a combined collection-destination intent phrase.
        assert len(query_calls) == len(aliases) * 2
        assert query_calls == [use_core.STRUCTURAL_RETRIEVAL_TOP_K] * len(aliases) * 2
        assert len(embedding_calls) == len(aliases) * 2
        assert all(
            any(alias.casefold() in query.casefold() for alias in aliases)
            for query in embedding_calls
        )

        # Pathways is the largest alias set in the canonical registry.
        if collection_name == "pathways":
            assert len(query_calls) == 8
            assert sum(query_calls) == 384
