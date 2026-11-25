"""Contract tests for runtime-aligned registry-to-renderer capability reporting."""
import pytest

from gold_star_capability_audit import build_capability_audit


def test_audit_joins_runtime_family_from_qualitative_review_by_benchmark_id():
    report = build_capability_audit(
        {"records": [
            {"benchmark_id": "supported", "status": "USER_APPROVED_GOLD_STANDARD",
             "gold_star_capabilities": {"deterministic_fallback_eligible": True}},
            {"benchmark_id": "unsupported", "status": "USER_APPROVED_GOLD_STANDARD",
             "gold_star_capabilities": {"deterministic_fallback_eligible": True}},
            {"benchmark_id": "missing-review", "status": "USER_APPROVED_GOLD_STANDARD",
             "gold_star_capabilities": {"deterministic_fallback_eligible": True}},
            {"benchmark_id": "superseded", "status": "SUPERSEDED_GOLD_STANDARD",
             "gold_star_capabilities": {"deterministic_fallback_eligible": True}},
            {"benchmark_id": "not-eligible", "status": "USER_APPROVED_GOLD_STANDARD",
             "gold_star_capabilities": {"deterministic_fallback_eligible": False}},
        ]},
        {"entries": [
            {"benchmark_id": "supported",
             "reasoning_family": "ethical_tradeoff_and_conflicting_harms"},
            {"benchmark_id": "unsupported", "reasoning_family": "unreviewed_family"},
        ]},
    )

    assert report["eligible_record_count"] == 4
    assert report["superseded_eligible_record_count"] == 1
    assert report["runtime_eligible_record_count"] == 3
    assert report["runtime_eligible_missing_review_count"] == 1
    assert report["runtime_eligible_missing_family_count"] == 0
    assert report["runtime_eligible_named_family_record_count"] == 2
    assert report["runtime_eligible_renderer_supported_record_count"] == 1
    assert report["runtime_eligible_renderer_unsupported_record_count"] == 1
    assert report["supported_families"][0]["plan_id"] == "ethical_tradeoff_v1"
    assert report["unsupported_families"][0]["reasoning_family"] == "unreviewed_family"


def test_audit_rejects_malformed_registry_and_review_containers():
    with pytest.raises(ValueError, match="registry.records must be a list"):
        build_capability_audit({"records": {}}, {"entries": []})
    with pytest.raises(ValueError, match="transfer_review.entries must be a list"):
        build_capability_audit({"records": []}, {"entries": {}})


def test_audit_rejects_duplicate_review_identity():
    with pytest.raises(ValueError, match="duplicate transfer-review benchmark_id"):
        build_capability_audit(
            {"records": []},
            {"entries": [
                {"benchmark_id": "duplicate", "reasoning_family": "one"},
                {"benchmark_id": "duplicate", "reasoning_family": "two"},
            ]},
        )
