"""Regression tests for the default Gold Star architecture and cross-question lesson formulation."""

import json
from pathlib import Path

import general_guide_composition as composition

ROOT = Path(__file__).resolve().parents[1]
QUERY = (
    "Several visitors ask different questions that expose the same recurring reasoning "
    "weakness. How should USE recognize the shared pattern and formulate a candidate Gold Star lesson?"
)
EXPECTED_OPENING = "Different questions reveal the same reasoning weakness"


def test_gold_star_structural_template_is_default_in_both_live_and_editorial_prompts():
    source = (ROOT / "general_guide_composition.py").read_text(encoding="utf-8")
    assert source.count("default structural template across every visitor-facing Guide path") == 1
    assert source.count("default structural template, not a universal subject-matter template") == 0
    assert source.count("QUESTION-FIRST, DEFAULT GOLD STAR STRUCTURAL TEMPLATE") == 2
    assert "SYSTEM-WIDE GOLD STAR STRUCTURAL TEMPLATE (default across the entire Guide)" in source
    assert "Subject adaptation changes what each structural move contains; it does not make the default architecture optional." in source
    compact_start = source.index("_GENERAL_GUIDE_SYSTEM_COMPACT =")
    compact_end = source.index("\n\n_GENERAL_GUIDE_SYSTEM =", compact_start)
    compact = source[compact_start:compact_end]
    assert "default structural template across every visitor-facing Guide path" in compact
    assert "specialist routes, retrieval-grounded composition, deterministic recovery, provider-exhaustion fallback" in compact


def test_cross_question_pattern_learning_query_has_provider_independent_gold_standard_recovery():
    result = composition._cross_question_pattern_learning_recovery(QUERY)
    assert result is not None
    paragraphs = [p.strip() for p in result["response"].split("\\n\\n") if p.strip()]
    assert len(paragraphs) == 3
    assert paragraphs[0].startswith(EXPECTED_OPENING)
    assert "consented and de-identified examples" in paragraphs[1]
    assert "human reviewer" in paragraphs[2]
    assert result["doorway_title"] == ""
    assert result["doorway_url"] == ""
    assert result["provider"] == "bounded_cross_question_pattern_learning_recovery"


def test_cross_question_pattern_learning_recovery_is_narrow_and_does_not_capture_neighbors():
    assert composition._cross_question_pattern_learning_recovery(
        "Several visitors ask different questions about stewardship. What resources should they read?"
    ) is None
    assert composition._cross_question_pattern_learning_recovery(
        "What is a Gold Star lesson for reasoning about uncertainty?"
    ) is None
    assert composition._cross_question_pattern_learning_recovery(
        "How should one visitor's reasoning weakness be corrected?"
    ) is None


def test_compose_returns_cross_question_learning_answer_without_calling_provider_or_retrieval():
    result = composition.compose(use_core=None, query=QUERY, context_data={})
    assert result is not None
    assert result["provider"] == "bounded_cross_question_pattern_learning_recovery"
    assert result["response"].startswith(EXPECTED_OPENING)
    assert len([p for p in result["response"].split("\\n\\n") if p.strip()]) == 3


def test_cross_question_gold_star_registry_and_review_are_unique_and_reconciled():
    registry = json.loads((ROOT / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    review = json.loads((ROOT / "docs/qa/gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))
    benchmark_id = "general-guide-cross-question-pattern-learning-candidate-gold-star-2026-11-18"
    records = [r for r in registry["records"] if r.get("benchmark_id") == benchmark_id]
    reviews = [r for r in review["entries"] if r.get("benchmark_id") == benchmark_id]
    assert len(records) == 1
    assert len(reviews) == 1
    assert records[0]["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert records[0]["numbering_status"] == "UNASSIGNED"
    assert records[0]["gold_star_capabilities"]["active_quality_contributor"] is True
    assert records[0]["gold_star_capabilities"]["deterministic_fallback_eligible"] is True
    assert reviews[0]["activation"] == "active_quality_contributor"
    approved = [r for r in registry["records"] if r.get("status") == "USER_APPROVED_GOLD_STANDARD"]
    assert len(approved) == registry["integrity_audit"]["approved_gold_star_count"]
    assert len(registry["records"]) == registry["integrity_audit"]["registry_record_count"]
    assert sum(1 for r in approved if r.get("numbering_status") == "UNASSIGNED") == registry["integrity_audit"]["unassigned_approved_gold_star_count"]
    assert len({r["benchmark_id"] for r in approved}) == len(approved)
