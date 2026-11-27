import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "qa" / "gold_standard_registry.json"
FIXTURE = ROOT / "tests" / "fixtures" / "general_guide_pain_without_total_identity_gold_star.json"
BENCHMARK_ID = "general-guide-pain-without-total-identity-2026-11-27"


def test_user_approved_pain_identity_gold_star_is_frozen_exactly():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    records = [item for item in registry["records"] if item["benchmark_id"] == BENCHMARK_ID]
    assert len(records) == 1
    record = records[0]
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == fixture["query"]
    assert record["expected_response"] == fixture["expected_response"]
    assert record["expected_response"].count("\n\n") == 4
    assert record["rating"] is None
    assert record["assistant_assessment_out_of_10"] == 9.0
    assert record["explicit_user_elevation_approval"] is True
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert record["gold_star_capabilities"]["generation_class"] == "user_approved_structural_learning"
    assert record["doorway_status"] == "NOT_EVALUATED"
    assert record["expected_doorway"] is None
    assert "do not infer" in record["gold_star_capabilities"]["abstention_boundary"].casefold()
    assert fixture["transfer_boundary"] == record["transfer_boundary"]
    assert record["provenance"]["visible_continuation_title"] == fixture["visible_continuation_title"]
    assert record["expected_response"] == fixture["expected_response"]
