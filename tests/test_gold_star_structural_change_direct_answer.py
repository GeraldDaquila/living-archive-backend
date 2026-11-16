import json
from pathlib import Path

from general_guide_gold_standards import resolve_exact_gold_standard
from gold_star_lessons import active_quality_contribution, deterministic_fallback_contribution

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
BENCHMARK_ID = "gs-2026-11-17-structural-change-vs-disruption"
QUESTION = "How can one distinguish structural change from ordinary disruption?"
EXPECTED = """Structural change reorganizes the arrangements that shape how a system works; ordinary disruption interrupts or unsettles its activity without necessarily changing those arrangements.

A disruption can expose weaknesses, interrupt routines, or create pressure for reform. It may even trigger structural change, but the event itself is not the change: the decisive shift occurs only when the response alters how authority, incentives, dependencies, resources, or capabilities are organized. A dramatic or prolonged interruption can leave those arrangements untouched.

To assess a claimed change, look at ordinary operations after emergency measures and exceptional support have ended. Compare who can make decisions, how resources move, and which dependencies shape routine work before and after. If those differences continue to govern everyday choices, the system has been structurally changed; if operations return to their previous pattern once the disturbance passes, the disruption has ended without durable reorganization."""


def test_structural_change_gold_star_has_three_distinct_paragraph_functions():
    record = next(r for r in REGISTRY["records"] if r["benchmark_id"] == BENCHMARK_ID)
    paragraphs = record["expected_response"].split("\n\n")
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["numbering_status"] == "UNASSIGNED"
    assert len(paragraphs) == 3
    assert paragraphs[0].startswith("Structural change reorganizes")
    assert "may expose weaknesses" in paragraphs[1]
    assert "ordinary operations after emergency measures" in paragraphs[2]
    assert "the event itself is not the change" in paragraphs[1]
    assert "exceptional support have ended" in paragraphs[2]
    assert record["expected_response"] == EXPECTED


def test_exact_gold_star_and_bounded_transfer_are_available():
    exact = resolve_exact_gold_standard(QUESTION)
    assert exact["benchmark_id"] == BENCHMARK_ID
    assert exact["expected_response"] == EXPECTED
    related = "How can one distinguish structural change from ordinary disruption in an organization?"
    active = active_quality_contribution(related)
    deterministic = deterministic_fallback_contribution(related)
    assert active["benchmark_id"] == BENCHMARK_ID
    assert deterministic["benchmark_id"] == BENCHMARK_ID
    assert "expected_response" not in active
    assert "expected_response" not in deterministic


def test_gold_star_has_no_unverified_doorway_or_serial():
    exact = resolve_exact_gold_standard(QUESTION)
    assert exact["doorway_title"] == ""
    assert exact["doorway_url"] == ""
    record = next(r for r in REGISTRY["records"] if r["benchmark_id"] == BENCHMARK_ID)
    assert record.get("gold_star_number") is None
    assert record["numbering_unassigned_reason_code"] == "NO_SERIAL_ALLOCATION_REQUESTED"
