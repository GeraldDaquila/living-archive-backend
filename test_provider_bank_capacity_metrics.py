from provider_bank import capacity_metrics_snapshot

def test_capacity_snapshot_has_bounded_operational_fields():
    snap=capacity_metrics_snapshot()
    assert snap["inflight"] >= 0
    assert 0 <= snap["viable_provider_score"] <= 1
    assert 0 <= snap["recent_llm_success_rate"] <= 1
    assert 0 <= snap["recent_exhaustion_rate"] <= 1
