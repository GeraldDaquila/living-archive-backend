"""Regression coverage for bounded developmental-capacities comparison recovery."""

import general_guide_composition as composition


def test_difference_between_prompt_enters_conceptual_relationship_recovery_path():
    question = "What is the difference between growth, adaptation, maturity, and integration?"
    assert composition.is_conceptual_relationship_question(question)


def test_developmental_capacities_comparison_recovers_distinctions_and_relationship():
    answer = composition._conceptual_relationship_recovery(
        "What is the difference between growth, adaptation, maturity, and integration?"
    )

    assert answer
    lowered = answer.casefold()
    for term in ("growth", "adaptation", "maturity", "integration"):
        assert term in lowered
    assert "not a fixed sequence" in lowered
    assert "water scarcity" in lowered
    assert "general conceptual explanation" in lowered


def test_developmental_capacities_recovery_does_not_trigger_for_incomplete_subject_set():
    answer = composition._conceptual_relationship_recovery(
        "What is the relationship between growth, adaptation, and maturity?"
    )

    assert answer is None


def test_developmental_capacities_recovery_does_not_trigger_without_comparison_intent():
    answer = composition._conceptual_relationship_recovery(
        "Growth, adaptation, maturity, and integration are important."
    )

    assert answer is None
