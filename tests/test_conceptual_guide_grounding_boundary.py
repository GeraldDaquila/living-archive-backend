"""Regression tests for the final conceptual Guide grounding boundary.

These are structural source contracts: a conceptual question must not remain
eligible for generic prose merely because a weak or unrelated doorway exists.
"""
from pathlib import Path

MAIN = Path(__file__).resolve().parents[1] / "main.py"
SOURCE = MAIN.read_text(encoding="utf-8")


def _final_conceptual_gate():
    start = SOURCE.index(
        "# Final corpus-boundary invariant for conceptual/explanatory questions."
    )
    end = SOURCE.index(
        "# Expose a small, deterministic provenance contract", start
    )
    return SOURCE[start:end]


def test_conceptual_guard_covers_role_purpose_and_significance_queries():
    assert "_is_conceptual_explanatory_request(query)" in _final_conceptual_gate()
    for query in (
        "What is the role of trust in community stewardship?",
        "What is the purpose of reciprocity in a community?",
        "What is the significance of human development?",
    ):
        assert query in SOURCE


def test_conceptual_response_gate_requires_selected_canonical_source_body():
    gate = _final_conceptual_gate()
    assert "generation_authority_protected_docs" in gate
    assert "generation_evidence_docs" in gate
    assert "retrieved_documents" in gate
    assert "_conceptual_source_body" in gate
    assert "_conceptual_supported" in gate
    assert "_conceptual_coverage >= 0.75" in gate
    assert "len(_conceptual_terms) >= 3" in gate


def test_conceptual_response_gate_fails_closed_without_relevant_body_even_if_doorway_exists():
    gate = _final_conceptual_gate()
    assert "if not _conceptual_supported:" in gate
    assert "response = _archive_limitation_response()" in gate
    assert "authoritative_doorway = None" in gate
    assert 'composition_context["evidence_sufficiency_unavailable"] = True' in gate


def test_conceptual_response_gate_does_not_relabel_general_knowledge_as_archive_supported():
    gate = _final_conceptual_gate()
    assert "_conceptual_source_body" in gate
    assert "_conceptual_supported" in gate
    assert "answer_basis" not in gate  # provenance remains assigned downstream
