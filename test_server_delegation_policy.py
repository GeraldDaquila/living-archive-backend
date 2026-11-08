from provider_health_store import choose_server_route

def _s(role="primary", **x):
    v={"server_id":role+"-a","role":role,"updated_at":1000,"inflight":2,"viable_provider_score":.9,"recent_llm_success_rate":.9,"recent_exhaustion_rate":.05};v.update(x);return v

def test_healthy_assigned_preserves_7030_route():
    assert choose_server_route(_s(),_s("secondary"),now=1010)["route"]=="assigned"

def test_degraded_assigned_uses_materially_healthier_counterpart():
    a=_s(viable_provider_score=.2,recent_llm_success_rate=.2,recent_exhaustion_rate=.9,inflight=20)
    b=_s("secondary",viable_provider_score=.95,recent_llm_success_rate=.95,recent_exhaustion_rate=.01,inflight=1)
    assert choose_server_route(a,b,now=1010)["route"]=="counterpart"

def test_partial_degradation_without_material_advantage_stays_assigned():
    a=_s(viable_provider_score=.35,recent_llm_success_rate=.5,recent_exhaustion_rate=.5,inflight=10)
    b=_s("secondary",viable_provider_score=.4,recent_llm_success_rate=.55,recent_exhaustion_rate=.45,inflight=8)
    assert choose_server_route(a,b,now=1010)["route"]=="assigned"

def test_stale_shared_state_fails_closed_to_assigned():
    stale=_s("secondary",updated_at=900)
    assert choose_server_route(_s(),stale,now=1000)["reason"]=="counterpart_state_unknown"
