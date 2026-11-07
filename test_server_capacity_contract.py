
import time
from provider_health_store import sanitize_server_capacity, server_capacity_score

def _state(**overrides):
    value={"server_id":"primary-a","role":"primary","updated_at":1000.0,"inflight":2,"viable_provider_score":0.9,"recent_llm_success_rate":0.9,"recent_exhaustion_rate":0.05}
    value.update(overrides); return value

def test_capacity_accepts_bounded_operational_record():
    clean=sanitize_server_capacity(_state(),now=1010.0)
    assert clean["role"]=="primary" and clean["inflight"]==2
    assert server_capacity_score(clean)>0.8

def test_capacity_rejects_stale_and_invalid_role():
    assert sanitize_server_capacity(_state(updated_at=900.0),now=1000.0) is None
    assert sanitize_server_capacity(_state(role="mirror"),now=1010.0) is None

def test_capacity_clamps_untrusted_metrics():
    clean=sanitize_server_capacity(_state(inflight=999,viable_provider_score=4,recent_llm_success_rate=-2,recent_exhaustion_rate=3),now=1010.0)
    assert clean["inflight"]==100
    assert clean["viable_provider_score"]==1.0
    assert clean["recent_llm_success_rate"]==0.0
    assert clean["recent_exhaustion_rate"]==1.0

def test_healthier_server_scores_materially_higher():
    healthy=_state(server_id="secondary-b",role="secondary",viable_provider_score=.95,recent_llm_success_rate=.95,recent_exhaustion_rate=.02,inflight=1)
    degraded=_state(server_id="primary-a",viable_provider_score=.2,recent_llm_success_rate=.25,recent_exhaustion_rate=.8,inflight=20)
    assert server_capacity_score(healthy)>server_capacity_score(degraded)+0.4
