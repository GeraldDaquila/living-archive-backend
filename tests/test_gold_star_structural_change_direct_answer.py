import json
from pathlib import Path

from general_guide_gold_standards import resolve_exact_gold_standard
from gold_star_lessons import (
    active_quality_contribution,
    deterministic_fallback_contribution,
    select_lesson,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
BENCHMARK_ID = "gs-2026-11-17-structural-change-vs-disruption"
QUESTION = "How can one distinguish structural change from ordinary disruption?"
EXPECTED = (
    "Structural change alters the underlying arrangements that shape how a system works; "
    "ordinary disruption interrupts or unsettles the system without necessarily changing those arrangements.\n\n"
    "A disruption may interrupt services, delay operations, unsettle routines, or create temporary instability. "
    "Structural change goes deeper: it changes the rules, incentives, relationships, distribution of authority, "
    "resource flows, or capacities that determine how the system operates. A disruption can expose structural "
    "weaknesses or trigger structural change, but it does not become structural simply because it is dramatic, "
    "widespread, or prolonged.\n\n"
    "The distinction becomes clear by asking what remains different after the immediate disturbance passes. "
    "Have decision rights, incentives, dependencies, or resource allocations changed? Are new patterns sustained "
    "by altered arrangements rather than temporary effort? Who gains authority, who carries the costs, and what "
    "evidence shows the new pattern will persist? If the underlying conditions remain intact, the event is "
    "disruption; if those conditions are durably reorganized, structural change has occurred."
)


def test_structural_change_gold_star_exact_answer_and_number_are_canonical():
    record = next(r for r in REGISTRY["records"] if r["benchmark_id"] == BENCHMARK_ID)
    resolved = resolve_exact_gold_standard(QUESTION)
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record.get("gold_star_number") is None
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["numbering_unassigned_reason_code"] == "NO_SERIAL_ALLOCATION_REQUESTED"
    assert record["expected_response"] == EXPECTED
    assert resolved["benchmark_id"] == BENCHMARK_ID
    assert resolved["expected_response"] == EXPECTED
    assert resolved["doorway_title"] == ""
    assert resolved["doorway_url"] == ""


def test_structural_change_gold_star_transfers_only_bounded_structural_guidance():
    related = "How can one distinguish structural change from ordinary disruption in an organization?"
    contribution = active_quality_contribution(related)
    assert contribution is not None
    assert contribution["benchmark_id"] == BENCHMARK_ID
    assert contribution["authority_mode"] == "structural_guidance_only"
    assert "underlying arrangements" in contribution["discipline"]
    assert "expected_response" not in contribution
    assert "doorway" not in contribution


def test_structural_change_gold_star_is_eligible_for_deterministic_guidance_only():
    related = "How can one distinguish structural change from ordinary disruption in an organization?"
    contribution = deterministic_fallback_contribution(related)
    assert contribution is not None
    assert contribution["benchmark_id"] == BENCHMARK_ID
    assert contribution["authority_mode"] == "deterministic_structural_guidance_only"
    assert "scale, duration, novelty, or intensity" in contribution["abstention_boundary"]
    assert "expected_response" not in contribution


def test_structural_change_gold_star_abstains_on_unrelated_questions():
    selected = select_lesson("What is the weather forecast for tomorrow?")
    assert selected is None or selected["benchmark_id"] != BENCHMARK_ID


def test_guide_template_opens_with_the_answer_not_an_announcement():
    source = (ROOT / "general_guide_composition.py").read_text(encoding="utf-8")
    assert "Begin with the substance of the answer" in source
    assert "Avoid throat-clearing and formulaic meta-openings" in source
