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
