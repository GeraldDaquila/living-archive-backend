"""Visitor-boundary regression for ethical trade-off dispatch precedence."""

import ast
from pathlib import Path

from deterministic_answer_recovery import (
    _is_ethical_tradeoff,
    compose_recovery,
)
from general_guide_composition import (
    _requires_responsibility_boundary_answer,
    _responsibility_boundary_recovery,
    enforce_response_contracts,
)

ROOT = Path(__file__).parent
MAIN = (ROOT / "main.py").read_text(encoding="utf-8")
QUESTION = (
    "How should a community balance individual freedom with shared responsibility "
    "when a decision affects everyone?"
)


def test_freedom_and_shared_responsibility_is_classified_as_ethical_tradeoff():
    assert _is_ethical_tradeoff(QUESTION)


def test_registered_tradeoff_composer_addresses_the_actual_value_conflict():
    answer = compose_recovery(QUESTION)
    assert isinstance(answer, str)
    assert len(answer.split()) >= 65
    for phrase in (
        "individual freedom",
        "shared responsibility",
        "people who will be affected",
        "less restrictive alternatives",
        "proportionate",
        "question or appeal",
    ):
        assert phrase in answer.casefold()
    assert "feeling responsible for fixing it" not in answer.casefold()


def test_ethical_tradeoff_is_not_misclassified_as_personal_responsibility_boundary():
    assert not _requires_responsibility_boundary_answer(QUESTION)


def test_final_response_contract_preserves_specific_tradeoff_over_generic_responsibility_boundary():
    generic_candidate = _responsibility_boundary_recovery()
    answer = enforce_response_contracts(QUESTION, generic_candidate)
    for phrase in (
        "individual freedom",
        "shared responsibility",
        "people who will be affected",
        "less restrictive alternatives",
        "proportionate",
        "question or appeal",
    ):
        assert phrase in answer.casefold()
    assert "noticing that something is broken" not in answer.casefold()


def test_api_dispatches_ethical_tradeoff_before_broad_conceptual_recovery():
    tree = ast.parse(MAIN)
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_basic_inquiry_round1_deterministic_response"
    )
    source = ast.get_source_segment(MAIN, function)
    ethical = source.index('if _is_freedom_responsibility_conflict:')
    conceptual = source.index('_guide_composition._conceptual_relationship_recovery(query)')
    assert ethical < conceptual
    assert '_is_ethical_tradeoff_recovery(query)' in source
    assert r"\bindividual\s+freedom\b" in source
    assert r"\bshared\s+responsibility\b" in source
    assert '"provider": "bounded_ethical_tradeoff_recovery"' in source
    assert '_compose_ethical_tradeoff_recovery(query)' in source


def test_other_tradeoff_families_are_not_claimed_by_the_narrow_dispatch():
    funding_question = (
        "How should a community decide which of two competing priorities deserves "
        "funding when neither can be fully supported?"
    )
    assert _is_ethical_tradeoff(funding_question)
    assert "if _is_freedom_responsibility_conflict:" in MAIN


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__]))
