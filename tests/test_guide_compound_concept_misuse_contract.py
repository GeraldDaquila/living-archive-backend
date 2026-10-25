"""Regression tests for compound concept-and-misuse questions."""

import pytest

from general_guide_composition import (
    _has_concept_misuse_explanation,
    _requires_concept_misuse_explanation,
    enforce_response_contracts,
)


QUERY = "What is a leverage point, and why can it be misused?"

GENERIC_CHECKLIST = (
    "To understand why a leverage point, and why can it be misused, separate the immediate event "
    "from the conditions that made it more likely. Consider the evidence for each explanation, "
    "the incentives and constraints involved, and what other explanation could fit the same facts. "
    "These are ways to investigate the question, not conclusions about a particular case; a confident "
    "answer needs the relevant details."
)


def test_compound_definition_and_misuse_question_is_classified():
    assert _requires_concept_misuse_explanation(QUERY)
    assert _requires_concept_misuse_explanation(
        "What is a leverage point, and how can it be exploited?"
    )


def test_non_compound_definition_is_not_misclassified():
    assert not _requires_concept_misuse_explanation("What is a leverage point?")


def test_generic_investigation_checklist_fails_the_explanatory_contract():
    assert not _has_concept_misuse_explanation(QUERY, GENERIC_CHECKLIST)


def test_final_boundary_replaces_generic_checklist_with_three_paragraph_answer():
    result = enforce_response_contracts(QUERY, GENERIC_CHECKLIST)
    paragraphs = [part.strip() for part in result.split("\n\n") if part.strip()]
    assert len(paragraphs) == 3
    assert paragraphs[0].startswith("A leverage point is a place in a system")
    assert "For example" in paragraphs[1]
    assert "misused" in paragraphs[1]
    assert "accountable" in paragraphs[2].lower()
    assert _has_concept_misuse_explanation(QUERY, result)


def test_valid_compound_explanation_is_preserved():
    valid = (
        "A leverage point is a place in a system where a relatively small change can produce a much larger effect. "
        "It influences how other parts behave.\n\n"
        "For example, at work, a person who controls an information bottleneck can exploit that dependency "
        "to conceal problems and gain an advantage while others bear the costs.\n\n"
        "Responsible use makes consequences visible and remains accountable to affected people, with room for "
        "scrutiny, challenge, and correction."
    )
    assert _has_concept_misuse_explanation(QUERY, valid)
    assert enforce_response_contracts(QUERY, valid) == valid
