"""Regression tests for the shared site-wide source evidence contract."""
from source_evidence_contract import (
    normalize_source_url,
    resolve_source_documents,
    verify_source_document,
)


def test_url_identity_ignores_www_query_fragment_and_trailing_slash():
    assert normalize_source_url(
        "https://www.geralddaquila.com/analytical-procedure/?utm_source=test#top"
    ) == normalize_source_url("https://geralddaquila.com/analytical-procedure/")


def test_source_verification_uses_identity_and_substantive_body_not_exact_markers():
    expected = {
        "title": "Analytical Procedure",
        "url": "https://geralddaquila.com/analytical-procedure/",
    }
    document = {
        "title": "Analytical Procedure | Life.Understood.",
        "url": "https://www.geralddaquila.com/analytical-procedure/?ref=guide",
        "text": "Observation precedes judgment. Evidence is considered according to the question. "
                "Explanations are examined for coherence, boundaries, implications, and revision. " * 5,
    }
    result = verify_source_document(expected, document)
    assert result["verified"] is True
    assert result["reason"] == "canonical_identity_and_body_verified"


def test_source_verification_rejects_wrong_page_even_if_body_is_long():
    expected = {
        "title": "Analytical Procedure",
        "url": "https://geralddaquila.com/analytical-procedure/",
    }
    document = {
        "title": "Revision Protocol",
        "url": "https://geralddaquila.com/revision-protocol/",
        "text": "A substantive body. " * 100,
    }
    assert verify_source_document(expected, document)["reason"] == "canonical_url_mismatch"


def test_partial_retrieval_does_not_claim_archive_absence():
    expected = [
        {"title": "Analytical Procedure", "url": "https://geralddaquila.com/analytical-procedure/"},
        {"title": "Revision Protocol", "url": "https://geralddaquila.com/revision-protocol/"},
    ]
    documents = [{
        "title": "Analytical Procedure",
        "url": expected[0]["url"],
        "text": "Observe carefully, clarify the question, gather evidence, and examine boundaries. " * 8,
    }]
    result = resolve_source_documents(expected, documents, min_verified=1)
    assert result["verified"] is True
    assert result["status"] == "partial"
    assert result["verified_count"] == 1
    assert result["corpus_absence_proven"] is False
    assert "bounded retrieval miss" in result["absence_claim_boundary"]


def test_required_source_gate_is_explicit_and_independent_of_optional_sources():
    expected = [
        {"title": "Analytical Procedure", "url": "https://geralddaquila.com/analytical-procedure/"},
        {"title": "Discernment Foundations", "url": "https://geralddaquila.com/discernment-foundations/"},
        {"title": "Revision Protocol", "url": "https://geralddaquila.com/revision-protocol/"},
    ]
    docs = [
        {
            "title": source["title"],
            "url": source["url"],
            "text": (source["title"] + " establishes a substantive method of inquiry. ") * 20,
        }
        for source in expected[:2]
    ]
    result = resolve_source_documents(
        expected,
        docs,
        required_titles=("Analytical Procedure", "Discernment Foundations"),
        min_verified=2,
    )
    assert result["verified"] is True
    assert result["status"] == "partial"


def test_all_canonical_wordpress_body_retrieval_uses_shared_verification_gate():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
    assert source.count("verify_retrieved_source_document(") >= 2
    assert "The Guide canonical body verification rejected a fetched source" in source
    assert "The Guide canonical search source verification rejected a candidate" in source


def test_url_identity_rejects_nonstandard_ports_and_preserves_path_case():
    assert normalize_source_url("https://geralddaquila.com:444/analytical-procedure/") == ""
    assert normalize_source_url("https://geralddaquila.com/Analytical-Procedure/") != normalize_source_url(
        "https://geralddaquila.com/analytical-procedure/"
    )
