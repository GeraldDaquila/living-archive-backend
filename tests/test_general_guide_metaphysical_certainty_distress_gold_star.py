import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "qa" / "gold_standard_registry.json"
FIXTURE = ROOT / "tests" / "fixtures" / "general_guide_metaphysical_certainty_distress_gold_star.json"
BENCHMARK_ID = "general-guide-metaphysical-certainty-during-distress-2026-11-27"


def test_epistemic_distress_gold_star_is_frozen_and_structural_only():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    records = [item for item in registry["records"] if item["benchmark_id"] == BENCHMARK_ID]
    assert len(records) == 1
    record = records[0]
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == fixture["query"]
    assert record["expected_response"] == fixture["expected_response"]
    assert record["expected_response"].count("\n\n") == 2
    assert record["explicit_user_elevation_approval"] is True
    assert record["rating"] is None
    assert record["assistant_assessment_out_of_10"] == 8.6
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["runtime_transfer"] is True
    assert record["reasoning_family"] == "epistemic_humility_under_distress"
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert record["doorway_status"] == "NOT_EVALUATED"
    assert record["expected_doorway"] is None
    assert record["transfer_boundary"] == fixture["transfer_boundary"]
    assert registry["integrity_audit"]["approved_gold_star_count"] == 142
    assert registry["integrity_audit"]["registry_record_count"] == 182
