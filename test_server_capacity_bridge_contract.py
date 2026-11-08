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


def test_counterpart_capacity_ignores_local_and_stale(monkeypatch):
    now=1000.0
    fresh={"server_id":"secondary-test","role":"secondary","updated_at":now,"inflight":1,"viable_provider_score":1,"recent_llm_success_rate":1,"recent_exhaustion_rate":0}
    stale=dict(fresh,server_id="stale",updated_at=now-100)
    monkeypatch.setattr(store,"load_server_capacities",lambda timeout=None: {"primary-test":{"server_id":"primary-test","role":"primary","updated_at":now,"inflight":0,"viable_provider_score":1,"recent_llm_success_rate":1,"recent_exhaustion_rate":0},"secondary-test":fresh,"stale":stale})
    monkeypatch.setattr(store.time,"time",lambda:now)
    assert store.counterpart_server_capacity(role="primary",server_id="primary-test")["server_id"]=="secondary-test"


def test_stale_counterpart_is_not_selected(monkeypatch):
    now=1000.0
    stale={"server_id":"secondary-test","role":"secondary","updated_at":now-301,"inflight":1,"viable_provider_score":1,"recent_llm_success_rate":1,"recent_exhaustion_rate":0}
    monkeypatch.setattr(store,"load_server_capacities",lambda timeout=None: {"secondary-test":stale})
    monkeypatch.setattr(store.time,"time",lambda:now)
    assert store.counterpart_server_capacity(role="primary",server_id="primary-test") is None

def test_capacity_publish_failure_is_best_effort(monkeypatch):
    monkeypatch.setattr(store,"save_server_capacity",lambda *args,**kwargs: (_ for _ in ()).throw(RuntimeError("bridge down")))
    snapshot={"contract_version":"server-capacity-v1","state":{"server_id":"primary-test","role":"primary","updated_at":1000,"inflight":0,"viable_provider_score":1,"recent_llm_success_rate":1,"recent_exhaustion_rate":0}}
    store._background_capacity_worker(snapshot)


def test_server_route_preserves_assigned_when_viable():
    healthy={"server_id":"primary","role":"primary","updated_at":1000,"inflight":1,"viable_provider_score":.8,"recent_llm_success_rate":.9,"recent_exhaustion_rate":.05}
    remote=dict(healthy,server_id="secondary",role="secondary",viable_provider_score=1,recent_llm_success_rate=1)
    assert store.choose_server_route(healthy,remote,now=1000)["route"]=="assigned"

def test_server_route_requires_material_advantage():
    weak={"server_id":"primary","role":"primary","updated_at":1000,"inflight":20,"viable_provider_score":.2,"recent_llm_success_rate":.3,"recent_exhaustion_rate":.7}
    slight={"server_id":"secondary","role":"secondary","updated_at":1000,"inflight":18,"viable_provider_score":.35,"recent_llm_success_rate":.4,"recent_exhaustion_rate":.65}
    strong=dict(slight,viable_provider_score=.9,recent_llm_success_rate=.95,recent_exhaustion_rate=.02,inflight=1)
    assert store.choose_server_route(weak,slight,now=1000)["route"]=="assigned"
    assert store.choose_server_route(weak,strong,now=1000)["route"]=="counterpart"

def test_server_route_fails_closed_on_missing_or_stale_state():
    healthy={"server_id":"primary","role":"primary","updated_at":1000,"inflight":0,"viable_provider_score":1,"recent_llm_success_rate":1,"recent_exhaustion_rate":0}
    stale=dict(healthy,server_id="secondary",role="secondary",updated_at=699)
    assert store.choose_server_route(healthy,None,now=1000)["route"]=="assigned"
    assert store.choose_server_route(healthy,stale,now=1000)["route"]=="assigned"


def test_capacity_advisory_never_changes_assignment_without_valid_counterpart(monkeypatch):
    monkeypatch.setattr(store,"counterpart_server_capacity",lambda **kwargs: None)
    result=store.server_capacity_advisory({"inflight":0,"viable_provider_score":1,"recent_llm_success_rate":1,"recent_exhaustion_rate":0},role="primary",server_id="primary-test")
    assert result["route"]=="assigned"
    assert result["reason"]=="counterpart_state_unknown"


def test_capacity_advisory_requires_material_advantage_under_load(monkeypatch):
    local={"inflight":5,"viable_provider_score":.25,"recent_llm_success_rate":.35,"recent_exhaustion_rate":.6}
    now=1000.0
    remote={"server_id":"secondary","role":"secondary","updated_at":now,"inflight":1,"viable_provider_score":.95,"recent_llm_success_rate":.95,"recent_exhaustion_rate":.02}
    monkeypatch.setattr(store.time,"time",lambda: now)
    monkeypatch.setattr(store,"counterpart_server_capacity",lambda **kwargs: remote)
    result=store.server_capacity_advisory(local,role="primary",server_id="primary")
    assert result["route"]=="counterpart"


def test_four_condition_capacity_simulation(monkeypatch):
    now=1000.0
    base={"server_id":"primary","role":"primary","updated_at":now,"inflight":1,"viable_provider_score":.9,"recent_llm_success_rate":.95,"recent_exhaustion_rate":.02}
    healthy_remote={"server_id":"secondary","role":"secondary","updated_at":now,"inflight":1,"viable_provider_score":.95,"recent_llm_success_rate":.96,"recent_exhaustion_rate":.01}
    degraded_remote={"server_id":"secondary","role":"secondary","updated_at":now,"inflight":30,"viable_provider_score":.1,"recent_llm_success_rate":.2,"recent_exhaustion_rate":.8}
    stale_remote=dict(healthy_remote,updated_at=now-301)
    assert store.choose_server_route(base,healthy_remote,now=now)["route"]=="assigned"
    assert store.choose_server_route(base,degraded_remote,now=now)["route"]=="assigned"
    assert store.choose_server_route(base,stale_remote,now=now)["route"]=="assigned"
    assert store.choose_server_route(base,None,now=now)["route"]=="assigned"


def test_capacity_publication_rate_limit(monkeypatch):
    import provider_bank as bank
    monkeypatch.setattr(bank.time,"time",lambda:1000.0)
    monkeypatch.setattr(bank,"publish_server_capacity_async",lambda metrics: True)
    bank._capacity_last_published=0.0
    assert bank.refresh_server_capacity_state() is True
    assert bank.refresh_server_capacity_state() is False
