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


def test_water_boiling_point_accepts_temperature_question_paraphrase():
    result = main._established_general_knowledge_recovery(
        "At standard atmospheric pressure, what temperature does water boil at?"
    )
    assert result is not None
    assert result["fact_id"] == "water_boiling_point_sea_level"
    assert "100°C (212°F)" in result["response"]


def test_compound_cosmology_question_stays_in_conceptual_general_guide():
    query = "What is cosmology, and why does it matter to how people live?"
    assert main._is_conceptual_explanatory_request(query)
    assert not main._is_bounded_glossary_request(query, glossary_term="cosmology")


def test_simple_cosmology_definition_is_not_forced_into_compound_classifier():
    # The bounded glossary path remains available for a plain definition.
    assert not main._is_conceptual_explanatory_request("What does cosmology mean?")


def test_cosmology_provider_exhaustion_fallback_answers_the_actual_question():
    query = "What is cosmology, and why does it matter to how people live?"
    result = main._basic_inquiry_round1_deterministic_response(
        query, {}, {"context_blocks": ""}
    )
    assert result["provider"] == "bounded_archive_informed_cosmology_recovery"
    response = result["response"]
    assert len(response.split("\n\n")) == 3
    assert "Cosmology is an understanding" in response
    assert "separation-based worldview" in response
    assert "unity-informed worldview" in response
    assert "not labels for judging a person" in response
    assert result["doorway_title"] == ""


def test_cosmology_recovery_is_limited_to_lived_significance_questions():
    recovery = main._established_archive_cosmology_recovery(
        "What is cosmology, and why does it matter to how people live?"
    )
    assert recovery is not None
    assert recovery["recovery_id"] == "archive_informed_cosmology_lived_significance"
    assert len(recovery["response"].split("\n\n")) == 3
    assert main._established_archive_cosmology_recovery("What is cosmology?") is None
    assert main._established_archive_cosmology_recovery(
        "What is the cosmology of the Living Archive?"
    ) is None
