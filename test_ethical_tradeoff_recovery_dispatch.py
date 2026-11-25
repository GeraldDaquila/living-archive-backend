"""Visitor-boundary regression for ethical trade-off dispatch precedence."""

import ast
from pathlib import Path

from deterministic_answer_recovery import (
    _is_ethical_tradeoff,
    compose_recovery,
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


def test_api_dispatches_ethical_tradeoff_before_broad_conceptual_recovery():
    tree = ast.parse(MAIN)
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_basic_inquiry_round1_deterministic_response"
    )
    source = ast.get_source_segment(MAIN, function)
    ethical = source.index('if _is_ethical_tradeoff_recovery(query):')
    conceptual = source.index('_guide_composition._conceptual_relationship_recovery(query)')
    assert ethical < conceptual
    assert '"provider": "bounded_ethical_tradeoff_recovery"' in source
    assert '_compose_ethical_tradeoff_recovery(query)' in source


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__]))
