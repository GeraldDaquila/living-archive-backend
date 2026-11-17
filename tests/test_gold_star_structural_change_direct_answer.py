import json
from pathlib import Path

from general_guide_gold_standards import resolve_exact_gold_standard
from gold_star_lessons import active_quality_contribution, deterministic_fallback_contribution

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
BENCHMARK_ID = "gs-2026-11-17-structural-change-vs-disruption"
QUESTION = "How can one distinguish structural change from ordinary disruption?"


def test_structural_change_answer_is_retained_as_candidate_not_gold_star():
    record = next(r for r in REGISTRY["records"] if r["benchmark_id"] == BENCHMARK_ID)
    paragraphs = record["expected_response"].split("\n\n")
    assert record["status"] == "WITHDRAWN_PENDING_DOORWAY"
    assert record["numbering_status"] == "UNASSIGNED"
    assert len(paragraphs) == 3
    assert paragraphs[0].startswith("Structural change reorganizes")
    assert "may expose weaknesses" in paragraphs[1]
    assert "ordinary operations after emergency measures" in paragraphs[2]
    assert record["withdrawal"]["withdrawn_by_user"] is True
    assert record["withdrawal"]["withdrawn_at"] == "2026-11-17"


def test_withdrawn_candidate_has_no_exact_answer_or_adaptive_authority():
    assert resolve_exact_gold_standard(QUESTION) is None
    related = "How can one distinguish structural change from ordinary disruption in an organization?"
    assert active_quality_contribution(related) is None
    assert deterministic_fallback_contribution(related) is None


def test_reapproval_requires_a_verified_canonical_doorway():
    record = next(r for r in REGISTRY["records"] if r["benchmark_id"] == BENCHMARK_ID)
    assert record["expected_doorway"] is None
    assert record["doorway_status"] == "WITHDRAWN_PENDING_VERIFIED_CANONICAL_DOORWAY"
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["active_quality_contributor"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
