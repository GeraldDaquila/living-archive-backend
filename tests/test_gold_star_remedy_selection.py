"""Tests for separating Gold Star learning from engineering-layer defects."""

import json
from pathlib import Path

import general_guide_composition as composition

ROOT = Path(__file__).resolve().parents[1]
QUERY = (
    "How should USE distinguish a recurring weakness that deserves a new Gold Star "
    "from a weakness better addressed through improved retrieval, source metadata, "
    "or deterministic logic?"
)


def test_remedy_selection_recovery_covers_the_question_without_a_paragraph_count_contract():
    result = composition._gold_star_remedy_selection_recovery(QUERY)
    assert result is not None
    answer = result["response"]
    assert answer.startswith("USE should create a Gold Star only when")
    for marker in ("Diagnose the earliest failed layer", "improve retrieval", "source metadata", "deterministic logic", "residual failure", "human review", "If an engineering correction removes the failure, do not create a Gold Star."):
        assert marker in answer
    assert result["doorway_title"] == ""
    assert result["doorway_url"] == ""
    assert result["provider"] == "bounded_gold_star_remedy_selection_recovery"


def test_remedy_selection_recovery_accepts_close_paraphrase():
    paraphrase = (
        "When should USE promote a repeated defect into a Gold Star, rather than "
        "repairing retrieval, indexing metadata, or deterministic routing?"
    )
    result = composition._gold_star_remedy_selection_recovery(paraphrase)
    assert result is not None
    assert "earliest failed layer" in result["response"]


def test_remedy_selection_recovery_does_not_capture_adjacent_questions():
    assert composition._gold_star_remedy_selection_recovery(
        "How should USE improve retrieval when relevant sources are missing?"
    ) is None
    assert composition._gold_star_remedy_selection_recovery(
        "What metadata should a canonical Archive source contain?"
    ) is None
    assert composition._gold_star_remedy_selection_recovery(
        "Several visitors ask different questions that expose the same recurring reasoning weakness. "
        "How should USE recognize the shared pattern and formulate a candidate Gold Star lesson?"
    ) is None
    assert composition._gold_star_remedy_selection_recovery(
        "How should USE choose between three similar Gold Stars?"
    ) is None


def test_compose_dispatches_approved_remedy_selection_registry_reference():
    result = composition.compose(use_core=None, query=QUERY, context_data={})
    assert result is not None
    assert result["provider"] == "gold_standard_registry"
    assert result["model"] == "approved-reference"
    assert result["response"].startswith("USE should create a Gold Star only when")


def test_remedy_selection_meta_governance_is_in_both_provider_prompts():
    source = (ROOT / "general_guide_composition.py").read_text(encoding="utf-8")
    assert source.count("GOLD STAR REMEDY SELECTION (META-GOVERNANCE TASKS ONLY)") == 2
    assert source.count("Repair engineering defects first and evaluate only any remaining reasoning gap.") == 2


def test_remedy_selection_approved_record_has_unique_identity_and_reconciled_inventory():
    registry = json.loads((ROOT / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    benchmark_id = "general-guide-gold-star-remedy-selection-vs-engineering-defect-2026-11-18"
    records = [r for r in registry["records"] if r.get("benchmark_id") == benchmark_id]
    assert len(records) == 1
    record = records[0]
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == QUERY
    assert record["expected_response"].startswith("USE should create a Gold Star only when")
    assert record["expected_doorway"] is None
    assert record["doorway_status"] == "INTENTIONALLY_NONE_APPROVED"
    assert record["forbids_doorway"] is True
    assert record["numbering_status"] == "UNASSIGNED"
    assert "terminal visitor boundary" in record["provenance"]["evidence_boundary"]
    assert record["freeze_policy"] == "immutable_user_approved_gold_standard"
    assert record["runtime_transfer"] is True
    approved = [r for r in registry["records"] if r.get("status") == "USER_APPROVED_GOLD_STANDARD"]
    assert len(approved) == registry["integrity_audit"]["approved_gold_star_count"] == 117
    assert len(registry["records"]) == registry["integrity_audit"]["registry_record_count"] == 156
    assert len({r["benchmark_id"] for r in registry["records"]}) == len(registry["records"])
