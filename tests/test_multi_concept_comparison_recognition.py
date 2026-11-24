"""Regression tests for pairwise and enumerated multi-concept comparisons."""

from main import _comparative_subject_terms


def test_existing_pairwise_difference_phrase_remains_supported():
    assert _comparative_subject_terms(
        "What is the difference between growth and adaptation?"
    ) == ["growth", "adaptation"]


def test_four_concept_comparison_with_follow_on_relationship_clause():
    assert _comparative_subject_terms(
        "In an organization undergoing restructuring, how do growth, adaptation, "
        "maturity, and integration differ, and how do they reinforce one another?"
    ) == ["growth", "adaptation", "maturity", "integration"]


def test_three_concept_enumeration_is_recognized():
    assert _comparative_subject_terms(
        "How do growth, adaptation, and maturity differ?"
    ) == ["growth", "adaptation", "maturity"]


def test_unrelated_relational_question_does_not_invent_comparison_subjects():
    assert _comparative_subject_terms(
        "How can a team build trust and coordinate during a restructuring?"
    ) == []
