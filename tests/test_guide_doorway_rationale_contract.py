"""Regression tests for the Guide's public doorway response contract."""

from main import (
    _normalize_authoritative_recommendation,
    _prepare_visitor_doorway,
)


def test_verified_canonical_doorway_without_rationale_gets_honest_non_attributive_rationale():
    doorway = _prepare_visitor_doorway(
        {
            "title": "Trust Architecture: The Missing Infrastructure Behind Functional Societies",
            "url": "https://geralddaquila.com/2026/09/07/trust-architecture-the-missing-infrastructure-behind-functional-societies",
        }
    )

    assert doorway is not None
    assert doorway["title"].startswith("Trust Architecture")
    assert doorway["url"].startswith("https://geralddaquila.com/")
    assert "further point of exploration" in doorway["rationale"]
    assert "not a claim that the page is the source" in doorway["rationale"]


def test_existing_grounded_doorway_rationale_is_preserved():
    rationale = (
        "This cornerstone examines trust through accountability, transparency, "
        "consistency, and repair."
    )
    doorway = _prepare_visitor_doorway(
        {
            "title": "Trust Architecture",
            "url": "https://geralddaquila.com/trust-architecture/",
            "rationale": rationale,
        }
    )

    assert doorway is not None
    assert doorway["rationale"] == rationale


def test_invalid_off_domain_doorway_is_still_rejected():
    candidate = {
        "title": "Unverified destination",
        "url": "https://example.org/resource",
    }
    assert _normalize_authoritative_recommendation(candidate) is None
    assert _prepare_visitor_doorway(candidate) is None


def test_selector_normalization_does_not_invent_rationale():
    candidate = {
        "title": "Relevant Archive Resource",
        "url": "https://geralddaquila.com/relevant-archive-resource/",
    }
    assert _normalize_authoritative_recommendation(candidate) == candidate
