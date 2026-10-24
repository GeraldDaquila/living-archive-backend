"""Regression tests for the final conceptual Guide grounding boundary.

These are structural source contracts: a conceptual question must not remain
eligible for generic prose merely because a weak or unrelated doorway exists.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"
SOURCE = MAIN.read_text(encoding="utf-8")
LIMITATION_SOURCE = (ROOT / "guide_direct_attribute_evidence.py").read_text(encoding="utf-8")


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


def test_archive_limitation_is_honest_and_offers_a_non_claiming_next_step():
    start = LIMITATION_SOURCE.index("def archive_limitation_response():")
    end = LIMITATION_SOURCE.index("\n\ndef select_authoritative_doorway", start)
    response_contract = LIMITATION_SOURCE[start:end]
    assert "haven’t found enough support" in response_contract
    assert "within the Archive" in response_contract
    assert "outside knowledge" in response_contract
    assert "narrowing the question" in response_contract
    assert "recommendation" not in response_contract


def test_conceptual_questions_trigger_canonical_body_retrieval_even_when_initial_retrieval_looks_sufficient():
    supplement = SOURCE[SOURCE.index("def _guide_requires_canonical_subject_supplement"):SOURCE.index("def _guide_subject_supplement_limit")]
    assert "conceptual_inquiry=False" in supplement
    assert "or conceptual_inquiry" in supplement
    assert "_is_conceptual_explanatory_request(query)" in SOURCE[SOURCE.index("def _basic_inquiry_response"):SOURCE.index("# Recovery may establish a qualifying doorway")]
    assert "or _is_conceptual_explanatory_request(query)" in SOURCE[SOURCE.index("def _basic_inquiry_response"):SOURCE.index("# Recovery may establish a qualifying doorway")]


def test_conceptual_doorway_is_aligned_to_vetted_retrieved_canonical_evidence():
    start = SOURCE.index("if not recovery_insufficient and recovered_docs:")
    end = SOURCE.index("# Recovery may establish a qualifying doorway", start)
    recovery = SOURCE[start:end]
    assert "_guide_align_registered_discovery_doorway(" in recovery
    assert "_is_conceptual_explanatory_request(query)" in recovery
    assert "composition_context[\"authoritative_doorway\"] = evidence_doorway" in recovery


def test_conceptual_retrieval_keeps_the_central_concept_in_the_canonical_search_query():
    start = SOURCE.index("def _wordpress_search_canonical_candidates")
    end = SOURCE.index("def _guide_", start)
    searcher = SOURCE[start:end]
    assert "_is_conceptual_explanatory_request(query)" in searcher
    assert "focus_terms = list(_subject_terms(conceptual_match.group(1)))" in searcher
    assert "context_terms = list(_subject_terms(conceptual_match.group(2)))" in searcher
