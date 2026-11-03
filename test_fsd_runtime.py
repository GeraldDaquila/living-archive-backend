import pytest
from fsd_runtime import build_quantum_query, parse_evidence

def test_quantum_queries_use_only_mapped_responses():
    answers = [0,1,2,3,0,1,2,3,0,1]
    first = build_quantum_query(answers, "organization", "Q001_CORRESPONDENCE")
    second = build_quantum_query(answers, "organization", "Q002_CORRECTABILITY")
    assert "People notice it" in first
    assert "meaningful authority" not in first
    assert "meaningful authority" in second
    assert "Where might there be room" in second

def test_evidence_parser_accepts_only_canonical_site_urls():
    context = {"context_blocks": "Title: A Canonical Resource\nURL: https://geralddaquila.com/resource/\nContent: Evidence excerpt\n\n---\n\nTitle: External\nURL: https://example.com/page\nContent: Ignore"}
    result = parse_evidence(context)
    assert len(result) == 1
    assert result[0]["title"] == "A Canonical Resource"

def test_evidence_parser_rejects_insufficient_retrieval():
    assert parse_evidence({"context_blocks": "", "evidence_sufficiency_unavailable": True}) == []
    assert parse_evidence(None) == []

def test_evidence_parser_deduplicates_canonical_urls():
    block = "Title: A\nURL: https://geralddaquila.com/a/\nContent: text"
    result = parse_evidence({"context_blocks": block + "\n\n---\n\n" + block})
    assert len(result) == 1
