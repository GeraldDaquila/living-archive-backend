import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "qa" / "gold_standard_registry.json"
FIXTURE = ROOT / "tests" / "fixtures" / "general_guide_metaphysical_certainty_distress_gold_star.json"
BENCHMARK_ID = "general-guide-metaphysical-certainty-during-distress-2026-11-27"


def test_epistemic_distress_screenshot_is_retained_only_as_near_miss_regression():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert fixture["classification"] == "near_miss"
    assert fixture["status"] == "NEAR_MISS_NOT_APPROVED"
    assert fixture["freeze_policy"] == "negative_regression_example_only"
    assert fixture["runtime_transfer"] is False
    assert fixture["transferable_lesson"] is None
    assert fixture["numbering_status"] == "NOT_APPLICABLE"
    assert "collective-governance framework" in fixture["provenance"]["review_decision"]
    assert not any(item["benchmark_id"] == BENCHMARK_ID for item in registry["records"])
    assert registry["integrity_audit"]["approved_gold_star_count"] == 141
    assert registry["integrity_audit"]["registry_record_count"] == 181
    assert registry["integrity_audit"]["active_quality_contributor_count"] == 138
