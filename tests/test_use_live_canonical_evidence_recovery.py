"""Query-level tests for canonical live-site recovery after internal evidence gates."""

import main


def _document(title, url, text):
    return {"title": title, "url": url, "text": text}


def test_weak_internal_evidence_triggers_bounded_public_canonical_recovery(monkeypatch):
    query = "What makes institutions capable of learning from mistakes?"
    profile = main._base._inquiry_profile(query)
    assert profile.get("action") not in {"recommendation", "navigation"}
    weak = _document(
        "Institutional Learning",
        "https://geralddaquila.com/institutional-learning/",
        "Institutions and learning.",
    )
    recovered = _document(
        "Institutional Correctability",
        "https://geralddaquila.com/institutional-correctability/",
        (
            "Institutional correctability is the capacity to recognize error, "
            "make correction possible, learn from consequences, and revise "
            "structures without hiding responsibility. "
        ) * 5,
    )
    calls = []

    monkeypatch.setattr(
        main,
        "_original_fetch_canonical_context",
        lambda _query: {
            "intent": "TOPICAL_INQUIRY",
            "canonical_link_context": main._serialize_context_documents([weak]),
            "context_blocks": "",
            "evidence_sufficiency_unavailable": True,
        },
    )

    def fake_expand(query_arg, seed_docs, index, core):
        calls.append((query_arg, list(seed_docs), index, core))
        return [dict(recovered, source_body_verified=True, source="public_living_archive_canonical_evidence_bridge")]

    monkeypatch.setattr(main.archive_crosslink, "expand_context", fake_expand)
    result = main._recommendation_first_fetch(query)

    assert len(calls) == 1
    assert calls[0][0] == query
    assert len(calls[0][1]) == 1
    assert "Institutional Correctability" in result["canonical_link_context"]
    assert "recognize error" in result["context_blocks"]
    assert result["evidence_sufficiency_unavailable"] is False


def test_sufficient_internal_evidence_keeps_primary_retrieval_and_skips_live_fallback(monkeypatch):
    query = "What makes institutions capable of learning from mistakes?"
    primary = _document(
        "Institutional Learning",
        "https://geralddaquila.com/institutional-learning/",
        (
            "Institutions learn from mistakes when they make errors visible, "
            "protect correction, examine consequences, and revise the rules "
            "that produced failure. "
        ) * 5,
    )
    monkeypatch.setattr(
        main,
        "_original_fetch_canonical_context",
        lambda _query: {
            "intent": "TOPICAL_INQUIRY",
            "canonical_link_context": main._serialize_context_documents([primary]),
            "context_blocks": "Internal canonical evidence is sufficient.",
            "evidence_sufficiency_unavailable": False,
        },
    )

    def forbidden_expand(*_args, **_kwargs):
        raise AssertionError("sufficient internal evidence must retain precedence")

    monkeypatch.setattr(main.archive_crosslink, "expand_context", forbidden_expand)
    result = main._recommendation_first_fetch(query)

    assert "Institutional Learning" in result["canonical_link_context"]
    assert result["context_blocks"] == "Internal canonical evidence is sufficient."


def test_metadata_only_crosslink_cannot_repair_failed_evidence_gate(monkeypatch):
    query = "What makes institutions capable of learning from mistakes?"
    weak = _document(
        "Institutional Learning",
        "https://geralddaquila.com/institutional-learning/",
        "Institutions and learning.",
    )
    metadata_only = {
        "title": "Institutional Correctability",
        "url": "https://geralddaquila.com/institutional-correctability/",
        "summary": "A navigation label only.",
        "content": "",
        "source_body_verified": False,
        "crosslink_mode": "territorial_navigation",
    }
    monkeypatch.setattr(
        main,
        "_original_fetch_canonical_context",
        lambda _query: {
            "intent": "TOPICAL_INQUIRY",
            "canonical_link_context": main._serialize_context_documents([weak]),
            "context_blocks": "Existing weak evidence only.",
            "evidence_sufficiency_unavailable": True,
        },
    )
    monkeypatch.setattr(main.archive_crosslink, "expand_context", lambda *_args, **_kwargs: [metadata_only])
    result = main._recommendation_first_fetch(query)
    assert result["evidence_sufficiency_unavailable"] is True
    assert result["context_blocks"] == "Existing weak evidence only."
    assert "Institutional Correctability" in result["canonical_link_context"]
