import main


QUERY = "What is the relationship between transparency and trust?"
DIRECT_TRUST_QUERY = "What is the role of trust in community stewardship?"


def test_unmapped_transparency_trust_relationship_is_recognized():
    assert main._is_transparency_trust_relational_synthesis_question(QUERY)
    assert not main._is_transparency_trust_relational_synthesis_question(DIRECT_TRUST_QUERY)


def test_terminal_boundary_clears_unapproved_doorway_aliases():
    doorway = {
        "title": "Trust Architecture: The Missing Infrastructure Behind Functional Societies",
        "url": "https://geralddaquila.com/2026/09/07/trust-architecture-the-missing-infrastructure-behind-functional-societies",
        "rationale": "A related resource.",
    }
    payload = {
        "response": "Transparency and trust are related but distinct.",
        "recommendation": doorway,
        "recommendations": [doorway],
        "canonical_doorway": doorway,
        "doorway": doorway,
        "authoritative_doorway": doorway,
        "canonical_recommendation": doorway,
        "archive_doorway": doorway,
        "recommendation_canonical_primary": doorway,
        "recommendation_canonical_secondary": doorway,
        "recommendation_canonical": doorway,
        "recommended_resource": doorway,
        "recommended_resources": [doorway],
        "doorway_title": doorway["title"],
        "doorway_url": doorway["url"],
        "doorway_rationale": doorway["rationale"],
        "recommendation_title": doorway["title"],
        "recommendation_url": doorway["url"],
    }

    result = main._guide_enforce_terminal_doorway_policy(payload, QUERY)

    for key in (
        "recommendation",
        "recommendations",
        "canonical_doorway",
        "doorway",
        "authoritative_doorway",
        "canonical_recommendation",
        "archive_doorway",
        "recommendation_canonical_primary",
        "recommendation_canonical_secondary",
        "recommendation_canonical",
        "recommended_resource",
        "recommended_resources",
        "doorway_title",
        "doorway_url",
        "doorway_rationale",
        "recommendation_title",
        "recommendation_url",
    ):
        assert result[key] is None, key
    assert result["doorway_decision"] == "omit"
    assert result["doorway_selection_status"] == "AUTHORIZED_OMISSION"
    assert result["doorway_selection_source"] == "unmapped_transparency_trust_relational_synthesis"
    assert result["navigation_suppressed_by_task_contract"] is True
    assert result["response"] == payload["response"]
