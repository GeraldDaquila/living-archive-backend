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
    assert standard["benchmark_id"] == "general-guide-retrieval-outage-deterministic-recovery-disclosure-gold-star-refined-2026-11-18"
    assert standard["forbids_doorway"] is True
    assert standard["doorway_title"] == ""
    assert "new search succeeded" in standard["expected_response"].casefold()
    assert len(standard["expected_response"].split("\n\n")) == 3


def test_provider_exhaustion_uses_the_exact_retrieval_outage_gold_star_without_context():
    question = "A retrieval service fails, but the Guide can still access previously verified source references and deterministic recovery mechanisms. What should it do, and what should it disclose?"
    result = main._basic_inquiry_provider_exhaustion_response(
        question, {}, {}, recommendation_available=False
    )
    assert result["provider"] == "gold_standard_registry_deterministic_fallback"
    assert "previously verified references remain accessible" in result["response"]
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
    parsed_evidence = main.use_core.context_blocks_to_documents(result["context_blocks"])
    assert parsed_evidence
    assert source in parsed_evidence[0]["text"]


def test_mirror_registry_request_does_not_repeat_wordpress_retrieval():
    doc = {
        "title": "Stewardship",
        "url": "https://geralddaquila.com/stewardship/",
        "text": "Verified published source body about responsibility and care.",
    }
    data = {
        "canonical_link_context": "Title: Stewardship\\nURL: https://geralddaquila.com/stewardship/\\nContent: Verified published source body about responsibility and care.",
        "context_blocks": "[Verified canonical source body]",
        "mirror_registry_active": True,
        "mirror_registry_count": 1,
        "mirror_source_body_count": 1,
        "mirror_orientation_metadata_only": False,
    }
    profile = {"risk": False, "action": "navigation", "grief": False}
    with (
        patch.object(main, "_PINECONE_RETRIEVAL_BYPASS", True),
        patch.object(main._base, "_inquiry_profile", return_value=profile),
        patch.object(main, "_mirror_registry_context", return_value=data),
        patch.object(main, "_parse_context_documents", return_value=[doc]),
        patch.object(main.archive_crosslink, "expand_context", side_effect=AssertionError("duplicate retrieval")),
        patch.object(main, "_general_guide_authoritative_doorway", return_value=None),
        patch.object(main, "_verified_archive_doorway_fallback", return_value=None),
    ):
        result = main._recommendation_first_fetch("Who or what is asking for responsible care through me?")

    assert result["mirror_source_body_count"] == 1
    assert result["mirror_orientation_metadata_only"] is False


def test_personal_stewardship_invitation_uses_bounded_answer_and_canonical_doorway():
    from deterministic_answer_recovery import (
        compose_recovery,
        has_registered_recovery,
        is_personal_stewardship_invitation_question,
    )

    query = "Who or what is asking for responsible care through me?"
    assert is_personal_stewardship_invitation_question(query)
    assert has_registered_recovery(query)

    answer = compose_recovery(query)
    assert "does not establish that a separate person" in answer
    assert "responsible care for what is entrusted to you" in answer
    assert "Care is not self-erasure or unlimited obligation" in answer
    assert len([part for part in answer.split("\n\n") if part.strip()]) == 3

    result = main._basic_inquiry_round1_deterministic_response(query, {}, {})
    assert result["provider"] == "bounded_personal_stewardship_invitation_recovery"
    assert result["recommendation"]["title"] == "Stewardship"
    assert result["recommendation"]["url"] == "https://geralddaquila.com/stewardship/"
    assert result["response"] == answer


def test_direct_comparison_doorway_search_does_not_fan_out_per_subject():
    query = "What is the difference between efficiency and effectiveness?"
    calls = []

    def search(candidate_query, *, limit=3):
        calls.append((candidate_query, limit))
        return []

    assert main._comparative_subject_terms(query) == ["efficiency", "effectiveness"]
    with (
        patch.object(main._base, "_inquiry_profile", return_value={"risk": False, "action": "none", "grief": False}),
        patch.object(main, "_wordpress_search_canonical_candidates", side_effect=search),
        patch.object(main, "_canonical_primary_from_docs", return_value=None),
        patch.object(main, "_is_conceptual_explanatory_request", return_value=False),
        patch.object(main, "_record_guide_fuzzy_shadow_comparison"),
    ):
        result = main._general_guide_authoritative_doorway(query, {})

    assert result is None
    # The original two-subject query is sufficient: single-subject results
    # would fail the direct-comparison evidence-fit gate and only add latency.
    assert calls == [(query, 3)]


def test_relationship_doorway_search_keeps_one_sided_subject_discovery():
    query = "What is the relationship between efficiency and effectiveness?"
    calls = []

    def search(candidate_query, *, limit=3):
        calls.append((candidate_query, limit))
        return []

    assert main._comparative_subject_terms(query) == ["efficiency", "effectiveness"]
    with (
        patch.object(main._base, "_inquiry_profile", return_value={"risk": False, "action": "none", "grief": False}),
        patch.object(main, "_wordpress_search_canonical_candidates", side_effect=search),
        patch.object(main, "_canonical_primary_from_docs", return_value=None),
        patch.object(main, "_is_conceptual_explanatory_request", return_value=False),
        patch.object(main, "_record_guide_fuzzy_shadow_comparison"),
    ):
        result = main._general_guide_authoritative_doorway(query, {})

    assert result is None
    # A relationship may be illuminated by a source that develops either side.
    assert calls == [
        (query, 3),
        ("efficiency", 10),
        ("effectiveness", 10),
    ]
