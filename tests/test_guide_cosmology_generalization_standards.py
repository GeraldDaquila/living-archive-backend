import pytest

from general_guide_composition import (
    _cosmology_generalization_standards_recovery,
    _has_cosmology_generalization_standards,
    _requires_cosmology_generalization_standards,
    enforce_response_contracts,
)


QUESTION = (
    "What standards should be met before The Guide generalizes from one archive "
    "text to the whole cosmology?"
)


def test_recognizes_cosmology_generalization_standards_without_overcapturing():
    assert _requires_cosmology_generalization_standards(QUESTION)
    assert not _requires_cosmology_generalization_standards(
        "What does this one Archive text say about cosmology?"
    )
    assert not _requires_cosmology_generalization_standards(
        "How do empirical inquiry and philosophy differ?"
    )


def test_generic_uncertainty_is_replaced_with_direct_methodological_standards():
    generic = (
        "The question deserves a direct answer, not a guess presented as certainty. "
        "The most useful next step is to identify the specific claim or outcome at issue, "
        "separate established facts from assumptions, and examine what evidence would "
        "distinguish plausible explanations. I don't have enough verified context to assert "
        "a case-specific conclusion, but the inquiry need not stop here."
    )
    recovered = enforce_response_contracts(QUESTION, generic)
    assert recovered != generic
    assert _has_cosmology_generalization_standards(recovered)
    assert len(recovered.split("\\n\\n")) == 3
    for concept in (
        "full context", "corroboration", "contradict", "traceable",
        "evidence warrants", "whole cosmology",
    ):
        assert concept in recovered.casefold()


def test_recovery_meets_the_contract():
    answer = _cosmology_generalization_standards_recovery()
    assert _has_cosmology_generalization_standards(answer)
    assert len(answer.split("\\n\\n")) == 3


def test_contract_accepts_complete_standards_and_rejects_single_paragraph():
    answer = _cosmology_generalization_standards_recovery()
    assert enforce_response_contracts(QUESTION, answer) == answer
    assert not _has_cosmology_generalization_standards(
        "Interpret the text carefully and seek more evidence before generalizing."
    )
