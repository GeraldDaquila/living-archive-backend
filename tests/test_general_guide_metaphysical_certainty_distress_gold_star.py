import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "qa" / "gold_standard_registry.json"
NEAR_MISS_FIXTURE = ROOT / "tests" / "fixtures" / "general_guide_metaphysical_certainty_distress_gold_star.json"
APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "general_guide_metaphysical_certainty_distress_response_gold_star.json"
NEAR_MISS_ID = "general-guide-metaphysical-certainty-during-distress-2026-11-27"
APPROVED_ID = "general-guide-metaphysical-certainty-distress-response-exemplar-2026-11-27"


def test_original_off_target_screenshot_remains_only_a_negative_regression():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    fixture = json.loads(NEAR_MISS_FIXTURE.read_text(encoding="utf-8"))
    assert fixture["classification"] == "near_miss"
    assert fixture["status"] == "NEAR_MISS_NOT_APPROVED"
    assert fixture["freeze_policy"] == "negative_regression_example_only"
    assert fixture["runtime_transfer"] is False
    assert fixture["transferable_lesson"] is None
    assert fixture["numbering_status"] == "NOT_APPLICABLE"
    assert "collective-governance framework" in fixture["provenance"]["review_decision"]
    assert not any(item["benchmark_id"] == NEAR_MISS_ID for item in registry["records"])


def test_user_elevated_compassionate_response_is_a_separate_frozen_gold_star_exemplar():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    fixture = json.loads(APPROVED_FIXTURE.read_text(encoding="utf-8"))
    record = next(item for item in registry["records"] if item["benchmark_id"] == APPROVED_ID)
    assert fixture["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert fixture["freeze_policy"] == "immutable_user_approved_gold_standard"
    assert fixture["user_reviewed_response"] is True
    assert fixture["explicit_user_elevation_approval"] is True
    assert fixture["assistant_assessment_out_of_10"] == 9.0
    assert fixture["runtime_transfer"] is False
    assert fixture["exact_answer_authority"] is False
    assert fixture["deterministic_fallback_eligible"] is False
    assert fixture["doorway_status"] == "TITLE_OBSERVED_URL_NOT_CAPTURED"
    assert fixture["expected_doorway"] is None
    assert fixture["numbering_status"] == "UNASSIGNED"
    assert fixture["reasoning_family"] == "compassionate_epistemic_grounding_during_metaphysical_distress"
    assert record["status"] == fixture["status"]
    assert record["query"] == fixture["query"]
    assert record["expected_response"] == fixture["expected_response"]
    assert record["provenance"]["source_date"] == "2026-11-27"
    assert "elevate to gold star" in record["elevation_approval_evidence"]
    assert record["gold_star_capabilities"]["generation_class"] == "user_approved_response_quality_exemplar"
    assert record["gold_star_capabilities"]["active_quality_contributor"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False


def test_registry_audit_counts_reconcile_without_changing_active_learning_population():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    approved = [item for item in registry["records"] if item["status"] == "USER_APPROVED_GOLD_STANDARD"]
    active = [item for item in approved if item.get("runtime_transfer") is True]
    assert len(approved) == 142
    assert len(registry["records"]) == 182
    assert len(active) == 138
    assert registry["integrity_audit"]["approved_gold_star_count"] == len(approved)
    assert registry["integrity_audit"]["registry_record_count"] == len(registry["records"])
    assert registry["integrity_audit"]["active_quality_contributor_count"] == len(active)
    assert registry["integrity_audit"]["approved_response_quality_exemplar_count"] == 2
