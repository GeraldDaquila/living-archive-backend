"""Regression tests for quoted-passage context restoration Gold Star."""

from general_guide_gold_standards import resolve_exact_gold_standard
from gold_star_lessons import active_quality_contribution, select_lesson
from general_guide_composition import _GENERAL_GUIDE_SYSTEM_COMPACT

QUESTION = (
    "A retrieved passage is quoted out of context in a user prompt. "
    "How should the Guide restore the surrounding context before analyzing it?"
)
BENCHMARK_ID = "general-guide-quoted-passage-context-restoration-gold-star-2026-11-18"


def test_quoted_context_gold_star_is_exactly_resolvable_with_relevant_doorway():
    standard = resolve_exact_gold_standard(QUESTION)
    assert standard is not None
    assert standard["benchmark_id"] == BENCHMARK_ID
    answer = standard["expected_response"].lower()
    for required in (
        "verify the original source", "preceding and following paragraphs",
        "compare the user's quotation", "what the source explicitly says",
        "only after that reconstruction", "keep any interpretation provisional",
    ):
        assert required in answer
    assert standard["doorway_title"] == (
        "The Living Archive Navigator: Volume III – Knowledge & Sensemaking"
    )
    assert standard["doorway_url"].endswith("/the-living-archive-navigator-volume-iii/")
    assert standard["doorway_rationale"]


def test_quoted_context_gold_star_contributes_bounded_transfer_discipline():
    selected = select_lesson(QUESTION)
    assert selected is not None
    assert selected["benchmark_id"] == BENCHMARK_ID
    assert selected["exact"] is True
    contribution = active_quality_contribution(QUESTION)
    assert contribution is not None
    assert contribution["benchmark_id"] == BENCHMARK_ID
    assert contribution["authority_mode"] == "structural_guidance_only"
    assert "adjacent paragraphs" in contribution["discipline"].lower()
    assert "analyze only after reconstruction" in contribution["discipline"].lower()
    assert "expected_response" not in contribution
    assert "doorway" not in contribution


def test_quoted_context_lesson_does_not_capture_unrelated_questions():
    for question in (
        "What is the central argument of this book?",
        "How should two archive passages with different emphases be synthesized?",
        "What does stewardship mean in everyday life?",
    ):
        selected = select_lesson(question)
        assert selected is None or selected["benchmark_id"] != BENCHMARK_ID


def test_compact_prompt_contains_bounded_context_restoration_contract():
    prompt = _GENERAL_GUIDE_SYSTEM_COMPACT
    assert "QUOTED-PASSAGE CONTEXT RESTORATION BEFORE INTERPRETATION" in prompt
    assert "Reconstruct first; analyze only afterward." in prompt
    assert "Apply this sequence only to genuine quotation-context tasks" in prompt


def test_semantic_ambiguity_gold_star_remains_registered_after_parallel_reconciliation():
    standard = resolve_exact_gold_standard(
        "Two sources use the same term differently. How should the Guide detect and explain the ambiguity before answering?"
    )
    assert standard is not None
    assert standard["benchmark_id"] == "general-guide-semantic-ambiguity-same-term-different-sources-gold-star-2026-11-18"


def test_parallel_gold_star_inventory_reconciles_across_registry_and_transfer_review():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    registry = json.loads((root / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    review = json.loads((root / "docs/qa/gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))
    approved = [r for r in registry["records"] if r.get("status") == "USER_APPROVED_GOLD_STANDARD"]
    active = [r for r in approved if r.get("runtime_transfer") is True and r.get("gold_star_capabilities", {}).get("active_quality_contributor") is True]
    assigned = [r for r in approved if r.get("numbering_status") == "ASSIGNED"]
    unassigned = [r for r in approved if r.get("numbering_status") == "UNASSIGNED"]
    review_ids = [e["benchmark_id"] for e in review["entries"] if e.get("activation") == "active_quality_contributor"]
    active_ids = {r["benchmark_id"] for r in active}
    assert len(registry["records"]) == 140
    assert "103 approved Gold Stars" in registry["last_reconciliation_note"]
    assert "101 active quality contributors" in registry["last_reconciliation_note"]
    assert len(approved) == registry["integrity_audit"]["approved_gold_star_count"] == 103
    assert len(active) == len(review_ids) == 101
    assert set(review_ids) == active_ids
    assert len(assigned) == registry["integrity_audit"]["numbered_gold_star_record_count"] == 38
    assert len(unassigned) == registry["integrity_audit"]["unassigned_approved_gold_star_count"] == 65
    assert len(assigned) + len(unassigned) == len(approved)
    assert len({r["benchmark_id"] for r in approved}) == len(approved)
    assert any(r["benchmark_id"] == BENCHMARK_ID for r in approved)
    assert any(r["benchmark_id"] == "general-guide-semantic-ambiguity-same-term-different-sources-gold-star-2026-11-18" for r in approved)
