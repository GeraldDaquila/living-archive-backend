"""Regression guards for the Trust doorway at the shared visitor boundary."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_trust_doorway_is_resolved_before_generic_retrieval_fallbacks():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    start = source.index("def _guide_restore_verified_doorway(payload, query):")
    end = source.index("\ndef ", start + 10)
    boundary = source[start:end]

    trust_guard = boundary.index(
        "and _is_trust_community_stewardship_question(query)"
    )
    generic_search = boundary.index("requires_independent_selection =")
    assert trust_guard < generic_search

    for field in (
        'safe["recommendation"] = trust_doorway',
        'safe["canonical_doorway"] = trust_doorway',
        'safe["authoritative_doorway"] = trust_doorway',
        'safe["doorway_title"] = trust_doorway["title"]',
        'safe["doorway_url"] = trust_doorway["url"]',
        'safe["doorway_rationale"] = trust_doorway["rationale"]',
        'safe["doorway_decision"] = "selected"',
        'safe["doorway_selection_status"] = "VERIFIED_RELEVANT_DESTINATION"',
        'safe["doorway_selection_evaluated"] = True',
        'safe["doorway_selection_source"] = "reviewed_trust_community_stewardship_contract"',
    ):
        assert field in boundary

    assert "exact_standard is None" in boundary
    assert "_trust_community_stewardship_canonical_recommendation(query)" in boundary
    assert "https://geralddaquila.com/trust-architecture/" in source


def test_trust_doorway_remains_separate_from_answer_in_live_guide_contract():
    controller = (
        ROOT
        / "wordpress/living-archive-answer-doorway-standard/assets/guide-controller-v489.329.js"
    ).read_text(encoding="utf-8")
    start = controller.index("function renderAuthoritativeRecommendation")
    end = controller.index("\nfunction ", start + 10)
    renderer = controller[start:end]

    assert "document.getElementById('archive-recommendation')" in renderer
    assert "container.replaceChildren(block)" in renderer
    assert "responseText.appendChild(block)" not in renderer
