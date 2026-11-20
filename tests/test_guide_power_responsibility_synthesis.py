import re
from pathlib import Path

from guide_power_responsibility import (
    compose_power_responsibility_relationship,
    is_power_responsibility_relationship_question,
)

def test_exact_power_responsibility_relationship_is_recognized():
    assert is_power_responsibility_relationship_question(
        "What is the relationship between power and responsibility?"
    )

def test_equivalent_relationship_wording_is_recognized():
    assert is_power_responsibility_relationship_question(
        "How are power and responsibility connected?"
    )

def test_co_mention_without_relationship_request_is_not_captured():
    assert not is_power_responsibility_relationship_question(
        "Give me examples of power and responsibility in public institutions."
    )

def test_answer_synthesizes_both_concepts_and_their_interaction():
    result = compose_power_responsibility_relationship(
        "What is the relationship between power and responsibility?"
    )
    assert result is not None
    answer = result["response"].casefold()
    for required in ("power and responsibility", "influence", "account", "formal",
                     "informal", "control", "capacity", "accountability"):
        assert required in answer
    assert len(answer.split()) >= 140
    assert answer.count("?") >= 1

def test_final_boundary_and_shared_composer_contract_are_wired():
    root = Path(__file__).resolve().parents[1]
    main = (root / "main.py").read_text(encoding="utf-8")
    composition = (root / "general_guide_composition.py").read_text(encoding="utf-8")
    assert "_compose_power_responsibility_relationship(query)" in main
    assert "final_visitor_boundary_power_responsibility_synthesis" in main
    assert "RELATIONAL SYNTHESIS CONTRACT" in composition
    assert "excerpts are evidence, not the answer" in composition
    assert 'safe["response_provenance"] = _final_response_provenance' in main
    assert '"class": "deterministic_by_design"' in main
    assert 'safe["answer_basis"] = _final_answer_basis' in main
    assert 'safe["evidence"] = []' in main
    assert '"source_evidence=not_attributed"' in main
    assert '_final_route["provider_present"] = False' in main
    assert '_floor_envelope["evidence"] = {' in main
    assert '_final_quality_floor["evidence_validation"] = _final_evidence_validation' in main
