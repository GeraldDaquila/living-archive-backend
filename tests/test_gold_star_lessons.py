import json
from pathlib import Path

import gold_star_lessons as lessons


def test_only_explicitly_approved_records_are_loaded():
    registry = json.loads((Path(__file__).resolve().parents[1] / "docs" / "qa" / "gold_standard_registry.json").read_text())
    approved = {
        r["benchmark_id"] for r in registry["records"]
        if r.get("subsystem") == "general-purpose-guide"
        and r.get("status") == "USER_APPROVED_GOLD_STANDARD"
        and r.get("benchmark_id") and r.get("query")
    }
    loaded = {x["id"] for x in lessons._EXEMPLARS}
    assert loaded <= approved
    assert loaded


def test_exact_approved_question_selects_structural_cue_only():
    result = lessons.select_exemplar("What is institutional memory, and why does it matter?")
    assert result is not None
    assert result["benchmark_id"] == "general-guide-institutional-memory-gold-standard-2026-10-26"
    guidance, token = lessons.build_exemplar_guidance("What is institutional memory, and why does it matter?")
    assert token == result["benchmark_id"]
    assert "structural cue only" in guidance
    assert "Do not copy the exemplar's answer" in guidance


def test_unrelated_question_abstains():
    result = lessons.select_exemplar("How do I calculate the area of a triangle?")
    assert result is None


def test_reconstructed_status_cannot_become_live_guidance():
    assert "USER_CONFIRMED_RECONSTRUCTION_NOT_HISTORICAL_EXACT" not in lessons._ALLOWED_STATUSES


def test_agency_and_circumstance_gold_star_is_transferable_but_bounded():
    exact = lessons.select_exemplar("What is the relationship between agency and circumstance?")
    assert exact is not None
    assert exact["benchmark_id"] == "general-guide-agency-circumstance-gold-star-2026-11-09"
    related = lessons.select_exemplar(
        "How should we understand personal responsibility when circumstances limit people's choices?"
    )
    assert related is not None
    assert related["benchmark_id"] == exact["benchmark_id"]
    assert lessons.select_exemplar("How do I calculate the area of a triangle?") is None
