"""Regression tests for narrow, deterministic elementary general-knowledge recovery."""

import main


def test_triangle_side_count_is_answered_as_general_knowledge():
    result = main._established_general_knowledge_recovery("How many sides does a triangle have?")
    assert result is not None
    assert result["fact_id"] == "triangle_has_three_sides"
    assert "three sides" in result["response"].lower()


def test_ice_floats_answer_explains_density():
    result = main._established_general_knowledge_recovery("Why does ice float in water?")
    assert result is not None
    assert result["fact_id"] == "ice_floats_because_less_dense"
    assert "less dense than liquid water" in result["response"].lower()


def test_elementary_fact_recovery_does_not_match_unrelated_questions():
    assert main._established_general_knowledge_recovery("What is the best way to govern a community?") is None
    assert main._established_general_knowledge_recovery("How many sides does a square have?") is None
    assert main._established_general_knowledge_recovery("Why does a boat float?") is None
