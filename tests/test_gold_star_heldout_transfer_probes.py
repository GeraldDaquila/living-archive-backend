"""Provider-free probes of existing Gold Star transfer across held-out phrasings.

These tests establish retrieval and structural-contribution eligibility only.
They do not establish provider composition, answer-quality improvement, or
causal adaptive transfer; those require separately authorized paired capture
and blind human review.
"""
import pytest

import gold_star_lessons


HELDOUT_PROBES = (
    (
        "relational_synthesis",
        "How do transparency and trust reinforce one another, and what limits that relationship?",
        "general-guide-relational-synthesis-concept-pairs-2026-11-24",
    ),
    (
        "organizational_learning",
        "Why do organizations repeat acknowledged failures even after publishing reviews?",
        "gs-2026-11-21-organizational-acknowledgment-without-learning",
    ),
    (
        "complicated_vs_complex",
        "How should we respond differently to a complicated problem and a complex one?",
        "gs-2026-11-20-complicated-complex-distinction",
    ),
    (
        "multicausal_systems_explanation",
        "How can we explain societal breakdown through interacting causes rather than one master cause?",
        "general-guide-systems-intelligibility-without-monocausal-reduction-gold-star-2026-11-13",
    ),
)


@pytest.mark.parametrize("family,query,expected_id", HELDOUT_PROBES)
def test_existing_gold_star_retrieves_for_heldout_paraphrase(family, query, expected_id):
    selected = gold_star_lessons.select_lesson(query)
    assert selected is not None, family
    assert selected["benchmark_id"] == expected_id, family
    assert selected["exact"] is False, family


@pytest.mark.parametrize("family,query,expected_id", HELDOUT_PROBES)
def test_heldout_retrieval_exposes_only_bounded_structural_guidance(
    family, query, expected_id
):
    contribution = gold_star_lessons.active_quality_contribution(query)
    assert contribution is not None, family
    assert contribution["benchmark_id"] == expected_id, family
    assert contribution["authority_mode"] == "structural_guidance_only"
    assert contribution["discipline"]
    assert contribution["abstention_boundary"]
    assert "expected_response" not in contribution
    assert "doorway" not in contribution


def test_unrelated_physical_science_probe_does_not_retrieve_a_community_rule_lesson():
    selected = gold_star_lessons.select_lesson(
        "Why does a metal spoon feel colder than a wooden spoon at the same room temperature?"
    )
    assert selected is None or selected["benchmark_id"] != (
        "gs-2026-11-23-community-rule-design-liberty-shared-obligations"
    )
