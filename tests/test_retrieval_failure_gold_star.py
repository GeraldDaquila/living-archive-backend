"""Regression tests for graceful recovery when canonical retrieval itself fails."""
from unittest.mock import patch
from pathlib import Path
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
    assert main._is_direct_comparison_query(query)
    assert not main._is_direct_comparison_query(
        "What is the relationship between efficiency and effectiveness?"
    )
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


def test_efficiency_effectiveness_difference_has_substantive_deterministic_recovery():
    from general_guide_composition import _conceptual_relationship_recovery

    query = "What is the difference between efficiency and effectiveness?"
    answer = _conceptual_relationship_recovery(query)
    assert answer
    assert len(answer.split()) >= 65
    assert "Efficiency is how economically a process uses resources" in answer
    assert "Effectiveness is whether the action produces the intended result" in answer
    assert "ineffective because" in answer

    result = main._basic_inquiry_round1_deterministic_response(query, {}, {})
    assert result["provider"] == "bounded_conceptual_relationship_recovery"
    assert result["response"] == answer


def test_recommendation_first_fetch_marks_request_scoped_doorway_search_attempt():
    query = "What is the difference between efficiency and effectiveness?"
    document = {
        "title": "A verified public resource",
        "url": "https://geralddaquila.com/example-resource/",
        "text": "A substantive source body about an unrelated subject.",
    }
    canonical_context = (
        "Title: A verified public resource\n"
        "URL: https://geralddaquila.com/example-resource/\n"
        "Content: A substantive source body about an unrelated subject."
    )
    token = main._GUIDE_CANONICAL_DOORWAY_SEARCH_ATTEMPTED.set(False)
    try:
        with (
            patch.object(main, "_PINECONE_RETRIEVAL_BYPASS", False),
            patch.object(main._base, "_inquiry_profile", return_value={"risk": False, "action": "none", "grief": False}),
            patch.object(main, "_original_fetch_canonical_context", return_value={
                "canonical_link_context": canonical_context,
                "context_blocks": canonical_context,
            }),
            patch.object(main, "_parse_context_documents", return_value=[document]),
            patch.object(main, "_general_guide_authoritative_doorway", return_value=None),
            patch.object(main, "_verified_archive_doorway_fallback", return_value=None),
        ):
            result = main._recommendation_first_fetch(query)

        assert result["canonical_doorway_search_attempted"] is True
        assert main._GUIDE_CANONICAL_DOORWAY_SEARCH_ATTEMPTED.get() is True
        with patch.object(
            main,
            "_wordpress_search_canonical_candidates",
            side_effect=AssertionError("duplicate canonical search attempted"),
        ):
            assert main._general_guide_authoritative_doorway(query, result) is None
    finally:
        main._GUIDE_CANONICAL_DOORWAY_SEARCH_ATTEMPTED.reset(token)


def test_terminal_doorway_boundary_does_not_repeat_an_attempted_search():
    query = "What is the difference between efficiency and effectiveness?"
    token = main._GUIDE_CANONICAL_DOORWAY_SEARCH_ATTEMPTED.set(True)
    try:
        with patch.object(main.use_core, "fetch_canonical_context") as fetch:
            result = main._boundary_canonical_doorway({"recommendation": None}, query)
        assert result is None
        fetch.assert_not_called()
    finally:
        main._GUIDE_CANONICAL_DOORWAY_SEARCH_ATTEMPTED.reset(token)


def test_terminal_fallback_does_not_treat_gold_star_retrieval_as_application(monkeypatch):
    question = (
        "How should an unfamiliar organizational problem be approached when "
        "the available evidence is incomplete?"
    )
    retrieval_calls = []

    def retrieved_but_not_applied(_query):
        retrieval_calls.append(_query)
        return {
            "benchmark_id": "reviewed-example",
            "discipline": "Separate observations from interpretations.",
            "abstention_boundary": "Do not infer causes without evidence.",
        }

    monkeypatch.setattr(
        main,
        "_gold_star_active_quality_contribution",
        retrieved_but_not_applied,
    )
    result = main._basic_inquiry_provider_exhaustion_response(
        question, {}, {}, recommendation_available=False
    )

    # The provider-exhaustion wrapper may relabel the deterministic approach
    # template as bounded provider-exhaustion recovery. It must not retrieve
    # provider-path Gold Star contributions or imply that retrieval was applied.
    assert retrieval_calls == []
    assert result["provider"] == "bounded_provider_exhaustion_recovery"
    assert result["response"].startswith(
        "Start by defining the outcome the change must achieve"
    )
    assert "Separate observations from interpretations." not in result["response"]
    assert "Do not infer causes without evidence." not in result["response"]


def test_default_evidence_recovery_rejects_single_generic_word_overlap():
    from general_guide_composition import _default_gold_standard_evidence_recovery

    question = (
        "Why does a metal spoon feel colder than a wooden spoon "
        "when both are at the same room temperature?"
    )
    unrelated = [
        "People sometimes feel more confident when a familiar story gives them a sense of direction.",
        "Some visitors feel uncertain when they encounter a new idea without a clear explanation.",
        "People may feel pressure to agree when others express a strong preference.",
        "An individual can feel pressure when outcomes depend on wider institutions and other people.",
        "People feel a need for belonging when their relationships and daily routines change.",
        "Someone may feel overwhelmed when several competing expectations arise at once.",
    ]
    documents = [{
        "title": "Unrelated reflections",
        "url": "https://geralddaquila.com/unrelated-reflections/",
        "content": " ".join(unrelated),
    }]

    assert _default_gold_standard_evidence_recovery(question, documents) is None


def test_default_evidence_recovery_requires_collective_query_term_coverage():
    from general_guide_composition import _default_gold_standard_evidence_recovery

    question = "How does stewardship support responsible care for shared resources?"
    relevant = [
        "Stewardship turns responsible care into explicit commitments for shared resources.",
        "Shared resources need stewardship rules that make responsible care observable.",
        "Responsible care for shared resources depends on stewardship and clear accountability.",
        "Good stewardship assigns care duties for shared resources to people with authority.",
        "Care for shared resources requires stewardship, fair participation, and review.",
        "Stewardship protects shared resources by making responsible care reciprocal.",
    ]
    documents = [{
        "title": "Stewardship and shared resources",
        "url": "https://geralddaquila.com/stewardship/",
        "content": " ".join(relevant),
    }]

    result = _default_gold_standard_evidence_recovery(question, documents)

    assert result is not None
    assert result["provider"] == "gold_standard_evidence_recovery"
    assert "Stewardship" in result["response"]
    assert "shared resources" in result["response"]



def test_guide_doorway_policy_remains_default_across_composition_prompt_layers():
    source = (
        Path(__file__).resolve().parents[1] / "general_guide_composition.py"
    ).read_text(encoding="utf-8")

    # The constitutional default must survive the general system prompt,
    # task-quality guidance, recovery guidance, and integrity-repair prompt.
    assert "A doorway is a separate but default part of the Guide's role:" in source
    assert "include one concise, verified, relevant Archive doorway separately by default." in source
    assert "include one concise, canonical Archive doorway by default" in source
    assert "Never substitute a generic Compass or use a doorway to rescue an off-target answer." not in source
    assert "use it only when it is itself a verified, honest, useful continuation." in source
    assert "A doorway is optional and follows the completed answer." not in source
    assert "optional, verified Living Archive" not in source
    assert "The answer must be complete before any optional doorway appears." not in source
    assert "The answer must be complete before any optional Archive doorway appears." not in source
    assert "offer a verified relevant doorway only when it materially advances the inquiry." not in source
    assert "offer a canonical Archive doorway only when" not in source
    assert "A doorway is a separate decision: include one only when a verified resource" not in source


def test_community_rule_doorway_fallback_resolves_exact_verified_barangay_resource():
    query = (
        "How should community rules and restrictions be justified when they limit "
        "personal liberty and freedom in the name of shared obligations and collective duties?"
    )
    expected_title = "The Barangay Before the State: Human-Scale Governance in Practice"
    expected_url = (
        "https://geralddaquila.com/2026/09/21/"
        "the-barangay-before-the-state-human-scale-governance-in-practice/"
    )

    selected = main._community_rule_design_canonical_doorway(query)
    fallback = main._verified_archive_doorway_fallback(query, [], None)

    assert selected is not None
    assert selected["title"] == expected_title
    assert selected["url"] == expected_url
    assert selected["rationale"]
    assert fallback is not None
    assert fallback["title"] == expected_title
    assert fallback["url"] == expected_url
