"""Regression tests for graceful recovery when canonical retrieval itself fails."""
from unittest.mock import patch
import main


def test_terminal_recovery_context_survives_retrieval_service_failure():
    with patch.object(main.use_core, "fetch_canonical_context", side_effect=RuntimeError("retrieval offline")):
        assert main._fetch_terminal_recovery_context("test question") == {}


def test_terminal_recovery_context_preserves_available_context():
    verified = {"context_blocks": "verified", "recommendation_canonical_primary": {"title": "Source", "url": "https://example.org/source"}}
    with patch.object(main.use_core, "fetch_canonical_context", return_value=verified):
        assert main._fetch_terminal_recovery_context("test question") is verified


def test_terminal_recovery_context_rejects_malformed_context():
    with patch.object(main.use_core, "fetch_canonical_context", return_value=["invalid"]):
        assert main._fetch_terminal_recovery_context("test question") == {}


def test_retrieval_outage_gold_star_is_exact_and_has_no_forced_doorway():
    from general_guide_gold_standards import resolve_exact_gold_standard
    question = "A retrieval service fails, but the Guide can still access previously verified source references and deterministic recovery mechanisms. What should it do, and what should it disclose?"
    standard = resolve_exact_gold_standard(question)
    assert standard is not None
    assert standard["benchmark_id"] == "general-guide-retrieval-outage-deterministic-recovery-disclosure-gold-star-2026-11-18"
    assert standard["forbids_doorway"] is True
    assert standard["doorway_title"] == ""
    assert "fresh search" in standard["expected_response"].casefold()
    assert len(standard["expected_response"].split("\n\n")) == 3


def test_provider_exhaustion_uses_the_exact_retrieval_outage_gold_star_without_context():
    question = "A retrieval service fails, but the Guide can still access previously verified source references and deterministic recovery mechanisms. What should it do, and what should it disclose?"
    result = main._basic_inquiry_provider_exhaustion_response(
        question, {}, {}, recommendation_available=False
    )
    assert result["provider"] == "gold_standard_registry_deterministic_fallback"
    assert "previously verified source references" in result["response"]
    assert result["recommendation"] is None


def test_mirror_registry_passes_verified_wordpress_body_as_evidence_not_metadata():
    source = (
        "Stewardship is the practice of responsible care. "
        "It includes boundaries, conscience, sustainability, and knowing "
        "what is yours to hold and what is not."
    )
    with patch.object(
        main.archive_crosslink,
        "expand_context",
        return_value=[{
            "title": "Stewardship",
            "url": "https://geralddaquila.com/stewardship/",
            "content": source,
            "text": source,
            "source_body_verified": True,
            "wp_id": "21767",
        }],
    ):
        result = main._mirror_registry_context("Who or what is asking for responsible care through me?")

    assert result["mirror_registry_count"] == 1
    assert result["mirror_source_body_count"] == 1
    assert result["mirror_orientation_metadata_only"] is False
    assert source in result["canonical_link_context"]
    assert "[Verified canonical source body" in result["context_blocks"]
    assert "metadata only" not in result["context_blocks"]
