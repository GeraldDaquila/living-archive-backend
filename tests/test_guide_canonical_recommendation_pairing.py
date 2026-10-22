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


def test_generic_governance_doorway_does_not_displace_specific_community_article():
    doorway = {
        "title": "Governance",
        "url": "https://geralddaquila.com/governance/",
    }
    assert main._healthy_community_recommendation_pair(doorway) is None


def test_governance_foundations_is_too_generic_for_healthy_community_question():
    doorway = {
        "title": "🏛️ Governance Foundations",
        "url": "https://geralddaquila.com/governance-foundations/",
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



def test_healthy_community_newcomer_is_not_practical_stewardship_fallback():
    query = (
        "I'm new to the Living Archive. I care about healthier communities, "
        "but I don't know its vocabulary or where to begin."
    )
    assert main._is_healthy_community_orientation_question(query)
    assert not main._is_practical_stewardship_question(query)


def test_healthy_community_recommendation_uses_exact_canonical_pair(monkeypatch):
    query = (
        "I'm new to the Living Archive. I care about healthier communities, "
        "but I don't know its vocabulary or where to begin."
    )
    expected = {
        "title": "What Healthy Communities Actually Look Like",
        "url": (
            "https://geralddaquila.com/2025/10/07/"
            "t4-codex-overflow-communities-governance-by-resonance/"
        ),
        "text": (
            "Healthy communities depend on participation, governance, belonging, "
            "shared responsibility, and meaningful voice in public life. "
            "Community governance needs participation and shared responsibility. "
            "Healthy communities make room for belonging, disagreement, and voice. "
            "People affected by decisions should be heard before shared rules change. "
        ) * 8,
        "kind": "archive_resource",
    }
    calls = []

    def fake_search(search_query, limit=10):
        calls.append((search_query, limit))
        if search_query == "What Healthy Communities Actually Look Like":
            return [dict(expected)]
        return []

    monkeypatch.setattr(main, "_wordpress_search_canonical_candidates", fake_search)
    generic_doorway = {
        "title": "ARK-006: Governance Protocols for Distributed Communities",
        "url": "https://geralddaquila.com/2026/05/10/ark-006-governance-protocols-for-distributed-communities/",
    }
    monkeypatch.setattr(main, "_general_guide_authoritative_doorway", lambda *_: generic_doorway)

    result = main._healthy_community_canonical_recommendation(query, {})
    assert result is not None
    assert result["title"] == expected["title"]
    assert result["url"] == expected["url"]
    assert calls, "Canonical WordPress retrieval should supply the candidate"


def test_healthy_community_direct_canonical_verification_avoids_search_fanout(monkeypatch):
    query = (
        "I'm new to the Living Archive. I care about healthier communities, "
        "but I don't know its vocabulary or where to begin."
    )
    preferred_title = "What Healthy Communities Actually Look Like"
    preferred_url = (
        "https://geralddaquila.com/2025/10/07/"
        "t4-codex-overflow-communities-governance-by-resonance/"
    )
    direct_body = {
        "title": preferred_title,
        "url": preferred_url,
        "text": (
            "Healthy communities depend on participation, governance, belonging, "
            "shared responsibility, and meaningful voice in public life. "
        ) * 8,
    }
    calls = {"fetch": [], "search": []}
    monkeypatch.setattr(main, "_general_guide_authoritative_doorway", lambda *_: None)

    def fetch(url):
        calls["fetch"].append(url)
        return dict(direct_body)

    def search(query, limit=10):
        calls["search"].append((query, limit))
        return []

    monkeypatch.setattr(main, "_wordpress_fetch_selected_canonical_body", fetch)
    monkeypatch.setattr(main, "_wordpress_search_canonical_candidates", search)

    result = main._healthy_community_canonical_recommendation(query, {})

    assert result == {
        "title": preferred_title,
        "url": preferred_url,
        "kind": "archive_resource",
    }
    assert calls["fetch"] == [preferred_url]
    assert calls["search"] == []


def test_healthy_community_direct_canonical_verification_failure_uses_existing_search_fallback(monkeypatch):
    query = (
        "I'm new to the Living Archive. I care about healthier communities, "
        "but I don't know its vocabulary or where to begin."
    )
    preferred_url = (
        "https://geralddaquila.com/2025/10/07/"
        "t4-codex-overflow-communities-governance-by-resonance/"
    )
    calls = {"fetch": [], "search": []}
    monkeypatch.setattr(main, "_general_guide_authoritative_doorway", lambda *_: None)
    monkeypatch.setattr(main, "_wordpress_fetch_selected_canonical_body", lambda url: calls["fetch"].append(url) or None)

    def search(query, limit=10):
        calls["search"].append((query, limit))
        if query == "What Healthy Communities Actually Look Like":
            return [{
                "title": "What Healthy Communities Actually Look Like",
                "url": preferred_url,
                "text": (
                    "Healthy communities depend on participation, governance, belonging, "
                    "shared responsibility, and meaningful voice in public life. "
                ) * 8,
                "kind": "archive_resource",
            }]
        return []

    monkeypatch.setattr(main, "_wordpress_search_canonical_candidates", search)
    result = main._healthy_community_canonical_recommendation(query, {})
    assert result is not None
    assert result["title"] == "What Healthy Communities Actually Look Like"
    assert result["url"] == preferred_url
    assert calls["fetch"] == [preferred_url]
    assert calls["search"]


def test_healthy_community_recommendation_rejects_unrelated_candidate(monkeypatch):
    query = (
        "I'm new to the Living Archive. I care about healthier communities, "
        "but I don't know its vocabulary or where to begin."
    )
    unrelated = {
        "title": "Learning to Receive Without Feeling Guilty",
        "url": "https://geralddaquila.com/2026/01/01/receiving/",
        "text": "Personal growth and receiving support can be difficult.",
    }
    monkeypatch.setattr(main, "_wordpress_search_canonical_candidates", lambda *_args, **_kwargs: [unrelated])
    monkeypatch.setattr(main, "_general_guide_authoritative_doorway", lambda *_: None)

    result = main._healthy_community_canonical_recommendation(query, {})
    assert result == {
        "title": "What Healthy Communities Actually Look Like",
        "url": (
            "https://geralddaquila.com/2025/10/07/"
            "t4-codex-overflow-communities-governance-by-resonance/"
        ),
        "kind": "archive_resource",
    }


def test_pure_navigation_is_not_reclassified_as_healthy_community_topic():
    assert not main._is_healthy_community_orientation_question(
        "Where should I begin with the Living Archive?"
    )
    assert main._is_navigator_orientation_request(
        "Where should I begin with the Living Archive?"
    )



def test_public_basic_inquiry_payload_carries_exact_canonical_recommendation(monkeypatch):
    query = (
        "I'm new to the Living Archive. I care about healthier communities, "
        "but I don't know its vocabulary or where to begin."
    )
    expected_url = (
        "https://geralddaquila.com/2025/10/07/"
        "t4-codex-overflow-communities-governance-by-resonance/"
    )
    evidence = {
        "title": "What Healthy Communities Actually Look Like",
        "url": expected_url,
        "text": (
            "Healthy communities depend on participation, governance, belonging, "
            "shared responsibility, voice, fair decision-making, and inclusion. "
            "Community governance requires participation. Shared responsibility "
            "means people affected by decisions have a meaningful voice. "
        ) * 8,
        "kind": "archive_resource",
    }
    monkeypatch.setattr(main, "_wordpress_search_canonical_candidates", lambda *_args, **_kwargs: [dict(evidence)])
    monkeypatch.setattr(main, "_general_guide_authoritative_doorway", lambda *_: None)
    monkeypatch.setattr(main, "_basic_inquiry_round1_requires_discovery", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(main, "_is_navigator_orientation_request", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(main, "_guide_requires_canonical_subject_supplement", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(main, "_guide_discovery_doorway_is_evidence_backed", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(main, "use_core.fetch_canonical_context", lambda _query: {
        "context_blocks": "",
        "canonical_link_context": "",
        "intent": "TOPICAL_INQUIRY",
    })
    monkeypatch.setattr(main.general_guide_composition, "is_practical_application_question", lambda _query: False)
    monkeypatch.setattr(main.general_guide_composition, "is_conceptual_relationship_question", lambda _query: False)
    monkeypatch.setattr(main, "_basic_inquiry_round1_deterministic_response", lambda *_args, **_kwargs: {
        "response": "A healthy community makes room for participation, disagreement, shared responsibility, and voice."
    })
    monkeypatch.setattr(main.general_guide_composition, "compose", lambda **_kwargs: {
        "response": "A healthy community makes room for participation, disagreement, shared responsibility, and voice.",
        "provider": "test",
        "model": "test",
        "response_shape": "test",
    })
    payload = main._basic_inquiry_response(query)
    assert payload["processing"] == "basic_inquiry"
    assert payload["response"]
    assert payload["recommendation"] == {
        "title": "What Healthy Communities Actually Look Like",
        "url": expected_url,
    }
