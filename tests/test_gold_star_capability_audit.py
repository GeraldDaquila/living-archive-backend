"""Contract tests for registry-to-renderer capability reporting."""
from gold_star_capability_audit import build_capability_audit


def test_audit_separates_registry_permission_from_renderer_support():
    report = build_capability_audit({
        "records": [
            {"benchmark_id": "supported", "reasoning_family": "ethical_tradeoff_and_conflicting_harms",
             "gold_star_capabilities": {"deterministic_fallback_eligible": True}},
            {"benchmark_id": "unsupported", "reasoning_family": "unreviewed_family",
             "gold_star_capabilities": {"deterministic_fallback_eligible": True}},
            {"benchmark_id": "missing-family",
             "gold_star_capabilities": {"deterministic_fallback_eligible": True}},
            {"benchmark_id": "not-eligible", "reasoning_family": "ethical_tradeoff_and_conflicting_harms",
             "gold_star_capabilities": {"deterministic_fallback_eligible": False}},
        ]
    })

    assert report["registry_record_count"] == 4
    assert report["eligible_record_count"] == 3
    assert report["eligible_missing_family_count"] == 1
    assert report["eligible_named_family_record_count"] == 2
    assert report["eligible_renderer_supported_record_count"] == 1
    assert report["eligible_renderer_unsupported_record_count"] == 1
    assert report["supported_families"][0]["plan_id"] == "ethical_tradeoff_v1"
    assert report["unsupported_families"][0]["reasoning_family"] == "unreviewed_family"


def test_audit_rejects_malformed_registry_records_container():
    import pytest

    with pytest.raises(ValueError, match="registry.records must be a list"):
        build_capability_audit({"records": {}})
