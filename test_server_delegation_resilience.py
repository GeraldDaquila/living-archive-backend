from provider_health_store import choose_server_route

def _s(role="primary", **x):
    v={"server_id":role+"-a","role":role,"updated_at":1000,"inflight":2,"viable_provider_score":.9,"recent_llm_success_rate":.9,"recent_exhaustion_rate":.05};v.update(x);return v

def test_provider_recovery_preserves_assigned_route():
    recovered=_s(viable_provider_score=.82,recent_llm_success_rate=.82,recent_exhaustion_rate=.08)
    assert choose_server_route(recovered,_s("secondary",viable_provider_score=.9),now=1010)["reason"]=="assigned_viable"

def test_both_degraded_without_clear_advantage_stays_assigned():
    a=_s(viable_provider_score=.25,recent_llm_success_rate=.3,recent_exhaustion_rate=.75,inflight=15)
    b=_s("secondary",viable_provider_score=.3,recent_llm_success_rate=.35,recent_exhaustion_rate=.7,inflight=14)
    assert choose_server_route(a,b,now=1010)["reason"]=="no_material_advantage"

def test_repeated_same_state_does_not_oscillate():
    a=_s(viable_provider_score=.2,recent_llm_success_rate=.2,recent_exhaustion_rate=.9,inflight=20)
    b=_s("secondary",viable_provider_score=.95,recent_llm_success_rate=.95,recent_exhaustion_rate=.01,inflight=1)
    decisions=[choose_server_route(a,b,now=1010)["route"] for _ in range(20)]
    assert decisions==["counterpart"]*20

def test_shared_state_interruption_fails_closed():
    a=_s()
    assert choose_server_route(a,None,now=1010)["route"]=="assigned"
