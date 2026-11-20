"""Structural integration checks for The Guide's epistemic retrieval planner."""
from pathlib import Path


def test_epistemic_planner_is_imported_by_production_guide():
    source = Path("main.py").read_text(encoding="utf-8")
    assert (
        "from guide_epistemic_query import build_epistemic_retrieval_plan "
        "as _build_epistemic_retrieval_plan"
    ) in source


def test_plan_is_applied_at_the_canonical_retrieval_boundary():
    source = Path("main.py").read_text(encoding="utf-8")
    start = source.index("def _basic_inquiry_response(query")
    end = source.index("\ndef _v48831_basic_inquiry_seam_self_audit", start)
    handler = source[start:end]

    plan_position = handler.index(
        "_epistemic_retrieval_plan = _build_epistemic_retrieval_plan(query)"
    )
    fetch_position = handler.index(
        "context_data = use_core.fetch_canonical_context(retrieval_query)"
    )
    assert plan_position < fetch_position
    assert "retrieval_query = resource_query" in handler
    assert (
        'retrieval_query = _epistemic_retrieval_plan["retrieval_query"]'
        in handler
    )
    assert "resource_query = _epistemic_retrieval_plan" not in handler


def test_evidence_validation_keeps_the_unexpanded_question():
    source = Path("main.py").read_text(encoding="utf-8")
    start = source.index("def _basic_inquiry_response(query")
    end = source.index("\ndef _v48831_basic_inquiry_seam_self_audit", start)
    handler = source[start:end]

    assert "use_core._evidence_sufficiency_gate(\n                recovered_docs, resource_query," in handler
    assert "use_core._v208_question_evidence_fit_gate(\n                    recovered_docs, resource_query," in handler


def test_original_question_remains_available_to_answer_and_doorway_logic():
    source = Path("main.py").read_text(encoding="utf-8")
    start = source.index("def _basic_inquiry_response(query")
    end = source.index("\ndef _v48831_basic_inquiry_seam_self_audit", start)
    handler = source[start:end]

    assert "_select_direct_attribute_doorway(\n            query," in handler
    assert "composition_result = general_guide_composition.compose(\n                use_core=use_core,\n                query=query," in handler
    assert "_basic_inquiry_round1_deterministic_response(\n                                query," in handler
