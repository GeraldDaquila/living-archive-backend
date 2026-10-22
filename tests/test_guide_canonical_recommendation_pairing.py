"""Regression tests for canonical recommendation title/URL pairing."""
import main


def test_relevant_community_resource_keeps_title_and_canonical_url():
    doorway = {
        "title": "What Healthy Communities Actually Look Like",
        "url": "https://geralddaquila.com/2025/10/07/t4-codex-overflow-communities-governance-by-resonance/",
        "kind": "archive_resource",
    }
    result = main._healthy_community_recommendation_pair(doorway)
    assert result is not None
    assert result["title"] == doorway["title"]
    assert result["url"] == doorway["url"]
    assert result["kind"] == "archive_resource"


def test_related_system_resource_can_qualify_without_exact_phrase_match():
    doorway = {
        "title": "The Human System",
        "url": "https://geralddaquila.com/2026/10/05/the-human-system/",
    }
    assert main._healthy_community_recommendation_pair(doorway) is not None


def test_unrelated_resource_is_not_presented_as_community_recommendation():
    doorway = {
        "title": "Learning to Receive Without Feeling Guilty",
        "url": "https://geralddaquila.com/2026/01/01/receiving/",
    }
    assert main._healthy_community_recommendation_pair(doorway) is None


def test_title_without_canonical_url_is_not_a_recommendation():
    assert main._healthy_community_recommendation_pair({
        "title": "What Healthy Communities Actually Look Like",
    }) is None


def test_non_archive_or_non_https_url_is_rejected():
    assert main._healthy_community_recommendation_pair({
        "title": "What Healthy Communities Actually Look Like",
        "url": "http://example.com/healthy-communities",
    }) is None


def test_exact_newcomer_query_matches_healthy_community_answer_and_canonical_pair():
    query = "I'm new to the Living Archive. I care about healthier communities, but I don't know its vocabulary or where to begin."
    doorway = {
        "title": "What Healthy Communities Actually Look Like",
        "url": "https://geralddaquila.com/2025/10/07/t4-codex-overflow-communities-governance-by-resonance/",
    }
    assert main._is_healthy_community_orientation_question(query)
    assert main._healthy_community_recommendation_pair(doorway) == doorway
    answer = main._healthy_community_answer_recovery()
    assert "participate" in answer
    assert "disagree" in answer
    assert "excluded or harmed" in answer


def test_unrelated_doorway_is_rejected_for_healthy_community_query():
    unrelated = {
        "title": "Learning to Receive Without Feeling Guilty",
        "url": "https://geralddaquila.com/2026/01/01/receiving/",
    }
    assert main._healthy_community_recommendation_pair(unrelated) is None


def test_living_archive_navigator_remains_distinct_from_healthy_community_resource():
    navigator = {
        "title": "Living Archive Navigator",
        "url": "https://geralddaquila.com/living-archive-navigator/",
    }
    assert main._healthy_community_recommendation_pair(navigator) is None


def test_existing_registry_discovery_selects_healthy_community_resource(monkeypatch):
    expected_title = "What Healthy Communities Actually Look Like"
    expected_url = "https://geralddaquila.com/2025/10/07/t4-codex-overflow-communities-governance-by-resonance/"
    node = {
        "node_id": "healthy-community-test",
        "title": expected_title,
        "canonical_url": expected_url,
        "purpose": "A guide to participation and governance in healthy communities",
        "semantic_hints": ["healthy communities", "community participation", "shared responsibility"],
        "status": "active",
    }
    body = {
        "title": expected_title,
        "url": expected_url,
        "text": (
            "Healthy communities depend on participation, shared responsibility, "
            "community voice, governance, and the ability to disagree safely. "
            "When exclusion or harm occurs, people need a fair way to raise concerns "
            "and participate in repairing the shared conditions."
        ),
    }
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [node])
    monkeypatch.setattr(main, "_wordpress_fetch_selected_canonical_body", lambda url: dict(body) if url == expected_url else None)
    monkeypatch.setattr(main, "_guide_discovery_evidence_grade", lambda subject, document, node=None: {"grade": "direct", "score": 120, "support": ["healthy", "communities"]})
    monkeypatch.setattr(main, "_guide_selected_doorway_discovery_evidence", lambda documents, subject, doorway: [dict(documents[0])])
    monkeypatch.setattr(main, "_guide_discovery_doorway_is_evidence_backed", lambda doorway, evidence: True)
    # The newcomer query must be shaped into the same subject used by ordinary
    # registered canonical discovery, rather than relying on incidental retrieval.
    query = "I'm new to the Living Archive. I care about healthier communities, but I don't know its vocabulary or where to begin."
    assert main._is_healthy_community_orientation_question(query)
    assert "healthy communities" == " ".join(["healthy", "communities"])
