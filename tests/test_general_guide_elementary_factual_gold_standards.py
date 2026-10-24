"""Regression contract for approved elementary factual Guide references."""

import json
from pathlib import Path

import main


FIXTURE = Path(__file__).parent / "fixtures" / "general_guide_elementary_factual_gold_standards.json"


def test_elementary_factual_gold_standard_fixture_is_versioned_and_additive():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert fixture["status"] == "PROPOSED_REFERENCE_FIXTURE"
    assert fixture["registry_id"] == "guide-elementary-general-knowledge-gold-standards-2026-10-25"
    assert {item["id"] for item in fixture["references"]} == {
        "triangle-has-three-sides",
        "ice-floats-because-less-dense",
    }


def test_triangle_gold_standard_response_matches_live_accepted_answer():
    result = main._established_general_knowledge_recovery("How many sides does a triangle have?")
    assert result is not None
    assert result["fact_id"] == "triangle_has_three_sides"
    assert result["response"] == "A triangle has three sides and three angles."


def test_ice_gold_standard_response_matches_live_accepted_answer():
    result = main._established_general_knowledge_recovery("Why does ice float in water?")
    assert result is not None
    assert result["fact_id"] == "ice_floats_because_less_dense"
    assert result["response"] == (
        "Ice floats in water because it is less dense than liquid water. "
        "When water freezes, its molecules form an open crystal structure that takes up more space, "
        "so the same mass occupies a larger volume."
    )


def test_factual_recovery_does_not_expand_to_unrelated_questions():
    assert main._established_general_knowledge_recovery("What is the best way to govern a community?") is None
    assert main._established_general_knowledge_recovery("How many sides does a square have?") is None
    assert main._established_general_knowledge_recovery("Why does a boat float?") is None
