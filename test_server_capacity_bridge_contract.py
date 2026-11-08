import provider_health_store as store

def test_capacity_snapshot_is_bounded_and_private():
    payload=store.build_server_capacity_snapshot({"inflight":999,"viable_provider_score":2,"recent_llm_success_rate":-1,"recent_exhaustion_rate":2},role="primary",server_id="primary-test",now=1000)
    assert payload["contract_version"]=="server-capacity-v1"
    state=payload["state"]
    assert state["inflight"]==100 and state["viable_provider_score"]==1.0
    assert state["recent_llm_success_rate"]==0.0 and state["recent_exhaustion_rate"]==1.0
    assert set(state)=={"server_id","role","updated_at","inflight","viable_provider_score","recent_llm_success_rate","recent_exhaustion_rate"}

def test_capacity_snapshot_requires_known_role_and_identity():
    assert store.build_server_capacity_snapshot({},role="unknown",server_id="x",now=1000) is None
    assert store.build_server_capacity_snapshot({},role="primary",server_id="",now=1000) is None
