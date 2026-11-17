"""Regression contract: the Guide remains an Archive doorway when verified evidence exists."""
import main


def test_verified_retrieved_resource_is_recovered_when_strict_selection_returns_none(monkeypatch):
    query = "How should The Guide distinguish archive-grounded guidance from general external knowledge?"
    docs = [{
        "title": "Archive Grounding and Interpretation",
        "url": "https://geralddaquila.com/archive-grounding-and-interpretation/",
        "text": "The Archive distinguishes direct claims from synthesis and orientation, keeping each traceable to its evidence.",
    }]
    profile = {"action": "topical", "grief": False}

    monkeypatch.setattr(main, "_canonical_primary_from_docs", lambda docs, query, profile: docs[0])
    monkeypatch.setattr(main, "_select_guide_node_fallback_doorway", lambda query: None)

    doorway = main._verified_archive_doorway_fallback(query, docs, profile)

    assert doorway == {
        "title": "Archive Grounding and Interpretation",
        "url": "https://geralddaquila.com/archive-grounding-and-interpretation/",
    }


def test_no_verified_evidence_keeps_no_doorway(monkeypatch):
    monkeypatch.setattr(main, "_canonical_primary_from_docs", lambda docs, query, profile: None)
    monkeypatch.setattr(main, "_select_guide_node_fallback_doorway", lambda query: None)

    # Suppression is legitimate only when no verified canonical continuation exists.
    assert main._verified_archive_doorway_fallback(
        "A question with no verified Archive continuation", [], {"action": "topical"}
    ) is None


def test_systemwide_answer_recovery_does_not_clear_verified_navigation():
    from pathlib import Path

    source = Path("main.py").read_text(encoding="utf-8")
    start = source.index("# System-wide Gold Standard recovery:")
    end = source.index("if len(_systemwide_paragraphs)", start)
    recovery_boundary = source[start:end]

    assert "Preserve an already verified doorway" in recovery_boundary
    assert "authoritative_doorway = None" not in recovery_boundary


def test_reflective_balance_question_opens_bounded_canonical_doorway_lookup(monkeypatch):
    query = "How can hope remain disciplined rather than naïve?"
    approved = {
        "title": "Hope, Discernment, and Responsible Action",
        "url": "https://geralddaquila.com/hope-discernment-responsible-action/",
        "purpose": "A canonical resource on disciplined hope and discernment under uncertainty.",
        "semantic_hints": ["hope", "disciplined", "discernment", "uncertainty"],
    }
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [approved])

    assert main._select_verified_doorway_conceptual_family(query) == "reflective_conceptual_balance"
    assert main._select_guide_node_fallback_doorway(query) == {
        "title": approved["title"],
        "url": approved["url"],
    }


def test_reflective_balance_question_does_not_invent_doorway_without_registry_evidence(monkeypatch):
    query = "How can hope remain disciplined rather than naïve?"
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [])

    assert main._select_verified_doorway_conceptual_family(query) == "reflective_conceptual_balance"
    assert main._select_guide_node_fallback_doorway(query) is None



def test_community_continuity_revision_recovers_its_verified_archive_doorway(monkeypatch):
    query = "How can communities preserve continuity while revising harmful inherited patterns?"
    assert main._is_conceptual_explanatory_request(query)
    assert main._select_verified_doorway_conceptual_family(query) == "community_continuity_revision"
    doorway = main._select_guide_node_fallback_doorway(query)
    assert doorway == {
        "title": "From Awakening to Stewardship",
        "url": "https://geralddaquila.com/from-awakening-to-stewardship/",
        "rationale": "This essay examines how communities and institutions carry wisdom and responsibility across generations while renewing structures and practices that no longer serve human flourishing. It distinguishes preserving what deserves to endure from preserving harmful patterns simply because they are inherited.",
    }

    monkeypatch.setattr(main, "_canonical_primary_from_docs", lambda docs, query, profile: None)
    recovered = main._verified_archive_doorway_fallback(query, [], {"action": "topical"})
    assert recovered == doorway



def test_community_continuity_recovery_is_registered_and_owns_its_verified_doorway():
    from deterministic_answer_recovery import (
        has_registered_recovery,
        registered_recovery_recommendation,
        compose_recovery,
    )

    query = "How can communities preserve continuity while revising harmful inherited patterns?"
    assert has_registered_recovery(query)
    assert registered_recovery_recommendation(query) == {
        "title": "From Awakening to Stewardship",
        "url": "https://geralddaquila.com/from-awakening-to-stewardship/",
    }
    answer = compose_recovery(query)
    assert answer.startswith("Communities preserve continuity")
    assert len([p for p in answer.split("\n\n") if p.strip()]) == 3


def test_provider_exhaustion_path_returns_registered_answer_and_doorway_together():
    from deterministic_answer_recovery import registered_recovery_recommendation

    query = "How can communities preserve continuity while revising harmful inherited patterns?"
    result = main._basic_inquiry_provider_exhaustion_response(
        query,
        {},
        {"context_blocks": ""},
        recommendation_available=True,
    )
    expected_doorway = registered_recovery_recommendation(query)
    assert result["response"].startswith("Communities preserve continuity")
    assert len([p for p in result["response"].split("\n\n") if p.strip()]) == 3
    assert result["recommendation"] == expected_doorway
    assert result["doorway_title"] == expected_doorway["title"]
    assert result["doorway_url"] == expected_doorway["url"]
