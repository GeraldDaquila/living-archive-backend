"""Provider-bank route batches shared health writes into one route-boundary snapshot."""
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import provider_bank
import provider_health_store as health_store


def _candidate(provider, model):
    return {
        "provider": provider,
        "model": model,
        "health_state": "healthy",
        "quality_failures": 0,
        "transport_failures": 0,
        "consecutive_failures": 0,
        "last_success": 100.0,
        "capabilities": ["json_object", "relational_analysis"],
    }


def test_multiple_candidate_failures_persist_one_shared_health_snapshot(monkeypatch):
    candidates = [_candidate("groq", "model-a"), _candidate("nvidia", "model-b")]
    monkeypatch.setattr(provider_bank, "select", lambda *args, **kwargs: candidates)
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_blocked", lambda state, operation=None: False)
    monkeypatch.setattr(provider_bank, "acquire_probe", lambda state: True)
    monkeypatch.setattr(provider_bank, "_STATE", {
        "models": {}, "quality": {}, "provider_cursor": 0, "model_cursors": {}
    })
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: 0.0)
    writes = []
    monkeypatch.setattr(provider_bank, "save_remote_states", lambda states: writes.append(states) or True)

    def fail_fast(use_core, item, messages, max_tokens, schema=None, timeout_override=None):
        raise provider_bank.ProviderCallError(
            "simulated independent lane 429",
            item["provider"], item["model"], 429, category="rate_limited"
        )

    monkeypatch.setattr(provider_bank, "_quota_guarded_call", fail_fast)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "user", "content": "synthetic calibration input"}],
        max_tokens=100,
        parse=provider_bank._json_object,
        operation="hrn_perception",
    )

    assert result is None
    assert len(writes) == 1
    assert set(writes[0]) >= {"groq:model-a", "nvidia:model-b"}
    assert provider_bank._PERSIST_CONTEXT.defer is False
    assert provider_bank._PERSIST_CONTEXT.dirty is False


def _reset_pending_persistence():
    with provider_bank._PENDING_SHARED_STATE_LOCK:
        provider_bank._PENDING_SHARED_STATE = False
        provider_bank._PENDING_SHARED_STATE_VERSION = 0
    provider_bank._PERSIST_CONTEXT.defer = False
    provider_bank._PERSIST_CONTEXT.dirty = False


def test_failed_route_flush_remains_pending_and_retries_at_next_boundary(monkeypatch):
    _reset_pending_persistence()
    monkeypatch.setattr(provider_bank, "_STATE", {
        "models": {"groq:model-a": {"provider": "groq", "model": "model-a"}},
        "quality": {},
        "provider_cursor": 0,
        "model_cursors": {},
    })
    writes = []
    outcomes = iter([False, True])

    def save(states):
        writes.append(states)
        return next(outcomes)

    monkeypatch.setattr(provider_bank, "save_remote_states", save)
    provider_bank._PERSIST_CONTEXT.defer = True
    provider_bank._PERSIST_CONTEXT.dirty = True

    provider_bank._route_result(None)
    assert len(writes) == 1
    assert provider_bank._PENDING_SHARED_STATE is True

    # A later route boundary retries even if that route had no new health event.
    provider_bank._route_result(None)
    assert len(writes) == 2
    assert provider_bank._PENDING_SHARED_STATE is False


def test_health_flush_serializes_an_immutable_record_snapshot(monkeypatch):
    _reset_pending_persistence()
    state = provider_bank.new_state("groq", "model-a")
    state["last_error"] = "captured-before-snapshot"
    monkeypatch.setattr(provider_bank, "_STATE", {
        "models": {"groq:model-a": state},
        "quality": {},
        "provider_cursor": 0,
        "model_cursors": {},
    })
    entered_export = threading.Event()
    release_export = threading.Event()
    writes = []
    original_export = provider_bank.export_health_states

    def paused_export(records):
        entered_export.set()
        assert release_export.wait(timeout=2)
        return original_export(records)

    monkeypatch.setattr(provider_bank, "export_health_states", paused_export)
    monkeypatch.setattr(provider_bank, "save_remote_states", lambda snapshot: writes.append(snapshot) or True)
    provider_bank._mark_shared_state_pending()

    with ThreadPoolExecutor(max_workers=1) as pool:
        flush = pool.submit(provider_bank._flush_pending_shared_state)
        assert entered_export.wait(timeout=1)
        # A concurrent transition after snapshot capture must not mutate the
        # record being serialized outside the provider-state lock.
        with provider_bank._STATE_LOCK:
            state["last_error"] = "changed-after-snapshot"
        release_export.set()
        assert flush.result(timeout=2) is True

    assert writes[0]["groq:model-a"]["last_error"] == "captured-before-snapshot"


def test_newer_dirty_version_is_not_cleared_by_older_successful_flush(monkeypatch):
    _reset_pending_persistence()
    monkeypatch.setattr(provider_bank, "_STATE", {
        "models": {"groq:model-a": {"provider": "groq", "model": "model-a"}},
        "quality": {},
        "provider_cursor": 0,
        "model_cursors": {},
    })
    writes = []

    def save(states):
        writes.append(states)
        if len(writes) == 1:
            # Simulate another route recording a new change while this snapshot
            # is in flight. Its newer version must survive the older ACK.
            provider_bank._mark_shared_state_pending()
        return True

    monkeypatch.setattr(provider_bank, "save_remote_states", save)
    provider_bank._mark_shared_state_pending()
    assert provider_bank._flush_pending_shared_state() is True
    assert len(writes) == 1
    assert provider_bank._PENDING_SHARED_STATE is True

    assert provider_bank._flush_pending_shared_state() is True
    assert len(writes) == 2
    assert provider_bank._PENDING_SHARED_STATE is False


# Shared bridge acknowledgement and serialization contract tests.


def _ack(*, submitted=2, written=2, success=True, version="v2"):
    return {
        "contract_version": version,
        "success": success,
        "submitted": submitted,
        "written": written,
    }


def test_full_exact_acknowledgement_is_accepted(monkeypatch):
    calls = []
    monkeypatch.setattr(
        health_store,
        "_request",
        lambda method, payload=None: calls.append((method, payload)) or _ack(),
    )
    states = {"groq:model-a": {"provider": "groq"}, "nvidia:model-b": {"provider": "nvidia"}}

    assert health_store.save_remote_states(states) is True
    assert calls[0][0] == "POST"
    assert calls[0][1]["contract_version"] == "v2"
    assert calls[0][1]["states"] == states


def test_zero_write_acknowledgement_is_rejected(monkeypatch):
    monkeypatch.setattr(health_store, "_request", lambda *args, **kwargs: _ack(submitted=1, written=0))
    assert health_store.save_remote_states({"groq:model-a": {}}) is False


def test_partial_write_acknowledgement_is_rejected(monkeypatch):
    monkeypatch.setattr(health_store, "_request", lambda *args, **kwargs: _ack(written=1))
    assert health_store.save_remote_states({"groq:model-a": {}, "nvidia:model-b": {}}) is False


def test_missing_or_wrong_contract_version_is_rejected(monkeypatch):
    monkeypatch.setattr(health_store, "_request", lambda *args, **kwargs: {"success": True, "submitted": 2, "written": 2})
    assert health_store.save_remote_states({"groq:model-a": {}, "nvidia:model-b": {}}) is False

    monkeypatch.setattr(health_store, "_request", lambda *args, **kwargs: _ack(version="v1"))
    assert health_store.save_remote_states({"groq:model-a": {}, "nvidia:model-b": {}}) is False


def test_missing_or_false_success_is_rejected(monkeypatch):
    monkeypatch.setattr(health_store, "_request", lambda *args, **kwargs: {"contract_version": "v2", "submitted": 2, "written": 2})
    assert health_store.save_remote_states({"groq:model-a": {}, "nvidia:model-b": {}}) is False

    monkeypatch.setattr(health_store, "_request", lambda *args, **kwargs: _ack(success=False))
    assert health_store.save_remote_states({"groq:model-a": {}, "nvidia:model-b": {}}) is False


def test_boolean_counts_are_rejected(monkeypatch):
    monkeypatch.setattr(health_store, "_request", lambda *args, **kwargs: _ack(submitted=True, written=True))
    assert health_store.save_remote_states({"groq:model-a": {}, "nvidia:model-b": {}}) is False


def test_mismatched_submitted_count_is_rejected(monkeypatch):
    monkeypatch.setattr(health_store, "_request", lambda *args, **kwargs: _ack(submitted=1, written=2))
    assert health_store.save_remote_states({"groq:model-a": {}, "nvidia:model-b": {}}) is False


def test_export_capacity_prefers_recent_states_with_deterministic_ties():
    states = {
        f"groq:model-{index:03d}": {
            "provider": "groq",
            "model": f"model-{index:03d}",
            "last_failure": float(index),
        }
        for index in range(101)
    }
    states["groq:tie-a"] = {"provider": "groq", "model": "tie-a", "last_failure": 200.0}
    states["groq:tie-b"] = {"provider": "groq", "model": "tie-b", "last_failure": 200.0}

    exported = health_store.export_health_states(states)
    keys = list(exported)

    assert len(exported) == 100
    assert keys[:2] == ["groq:tie-a", "groq:tie-b"]
    assert "groq:model-100" in exported
    assert "groq:model-000" not in exported


def test_behavioral_last_operation_is_exported():
    state = {
        "provider": "groq",
        "model": "model-a",
        "last_operation": "hrn_relational",
        "probe_successes": 7,
        "probe_in_flight": True,
    }
    exported = health_store.export_health_states({"groq:model-a": state})["groq:model-a"]

    assert exported["last_operation"] == "hrn_relational"
    assert "probe_successes" not in exported
    assert exported["probe_in_flight"] is False


def test_shared_health_read_rejects_wrong_contract_version(monkeypatch):
    monkeypatch.setattr(health_store, "_READ_CACHE", None)
    monkeypatch.setattr(health_store, "_READ_CACHE_UNTIL", 0.0)
    monkeypatch.setattr(
        health_store,
        "_request",
        lambda method, payload=None: {"contract_version": "v1", "states": {}},
    )
    assert health_store.load_remote_states() is None


def test_half_open_probe_claim_has_exactly_one_concurrent_owner():
    state = {"state": "half_open", "probe_in_flight": False}
    barrier = threading.Barrier(12)

    def claim():
        barrier.wait(timeout=2)
        return provider_bank.acquire_probe(state)

    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda _: claim(), range(12)))

    assert sum(bool(result) for result in results) == 1
    assert state["probe_in_flight"] is True


def test_provider_state_lock_is_released_before_bridge_network_write(monkeypatch):
    _reset_pending_persistence()
    monkeypatch.setattr(provider_bank, "_STATE", {
        "models": {"groq:model-a": provider_bank.new_state("groq", "model-a")},
        "quality": {},
        "provider_cursor": 0,
        "model_cursors": {},
    })
    acquired = threading.Event()

    def save(_states):
        def acquire_from_another_thread():
            with provider_bank._STATE_LOCK:
                acquired.set()

        worker = threading.Thread(target=acquire_from_another_thread)
        worker.start()
        worker.join(timeout=1)
        return acquired.is_set()

    monkeypatch.setattr(provider_bank, "save_remote_states", save)
    provider_bank._success("groq", "model-a", "generic")

    assert acquired.is_set()
    assert provider_bank._PENDING_SHARED_STATE is False


def _run_two_state_transitions(first, second):
    barrier = threading.Barrier(2)

    def run(callback):
        barrier.wait(timeout=2)
        callback()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run, callback) for callback in (first, second)]
        for future in futures:
            future.result(timeout=3)


def test_same_model_success_and_failure_transitions_remain_coherent(monkeypatch):
    _reset_pending_persistence()
    state = provider_bank.new_state("groq", "model-a")
    monkeypatch.setattr(provider_bank, "_STATE", {
        "models": {"groq:model-a": state},
        "quality": {},
        "provider_cursor": 0,
        "model_cursors": {},
    })
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: None)
    failure = provider_bank.ProviderCallError(
        "synthetic concurrent failure", "groq", "model-a", 429, category="rate_limited"
    )

    _run_two_state_transitions(
        lambda: provider_bank._failure(failure, "groq", "model-a", operation="generic"),
        lambda: provider_bank._success("groq", "model-a", "generic"),
    )

    assert state["state"] in {"healthy", "open"}
    if state["state"] == "healthy":
        assert state["failures"] == 0
        assert state["consecutive_failures"] == 0
        assert state["last_error"] == ""
    else:
        assert state["failures"] == 1
        assert state["consecutive_failures"] == 1
        assert state["last_error"] == "synthetic concurrent failure"


def test_provider_quarantine_and_sibling_success_are_atomic(monkeypatch):
    _reset_pending_persistence()
    primary = provider_bank.new_state("groq", "model-a")
    sibling = provider_bank.new_state("groq", "model-b")
    monkeypatch.setattr(provider_bank, "_STATE", {
        "models": {"groq:model-a": primary, "groq:model-b": sibling},
        "quality": {},
        "provider_cursor": 0,
        "model_cursors": {},
    })
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: None)
    failure = provider_bank.ProviderCallError(
        "synthetic account authentication failure",
        "groq",
        "model-a",
        401,
        category="authentication",
    )

    _run_two_state_transitions(
        lambda: provider_bank._failure(failure, "groq", "model-a", operation="generic"),
        lambda: provider_bank._success("groq", "model-b", "generic"),
    )

    if sibling["state"] == "healthy":
        assert sibling["category"] == ""
        assert sibling["quarantine_until"] == 0.0
    else:
        assert sibling["state"] == "open"
        assert sibling["category"] == "authentication"
        assert sibling["quarantine_until"] > 0.0


def test_quality_rejection_and_validated_success_are_atomic(monkeypatch):
    _reset_pending_persistence()
    model = provider_bank.new_state("groq", "model-a")
    quality_key = provider_bank._quality_key("hrn_relational", "groq", "model-a")
    quality = {
        "provider": "groq",
        "model": "model-a",
        "operation": "hrn_relational",
        "quality_failures": 0,
        "last_quality_failure": 0.0,
        "last_quality_success": 0.0,
        "quality_cooldown_until": 0.0,
        "quality_error": "",
    }
    monkeypatch.setattr(provider_bank, "_STATE", {
        "models": {"groq:model-a": model},
        "quality": {quality_key: quality},
        "provider_cursor": 0,
        "model_cursors": {},
    })
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: None)

    _run_two_state_transitions(
        lambda: provider_bank._record_quality_rejection(
            "groq", "model-a", "hrn_relational", "prescriptive-language"
        ),
        lambda: provider_bank._success("groq", "model-a", "hrn_relational"),
    )

    assert quality["quality_failures"] in {0, 1}
    if quality["quality_failures"] == 0:
        assert quality["quality_cooldown_until"] == 0.0
        assert quality["quality_error"] == ""
        assert quality["last_quality_success"] > 0.0
    else:
        assert quality["quality_cooldown_until"] > 0.0
        assert quality["quality_error"] == "prescriptive-language"


def test_newer_remote_failure_merges_operation_specific_cooldown_context():
    local = {
        "provider": "groq",
        "model": "model-a",
        "state": "healthy",
        "last_failure": 10.0,
        "last_success": 5.0,
        "last_operation": "general_guide_composition",
        "failures": 1,
        "consecutive_failures": 1,
        "cooldown_until": 20.0,
    }
    remote = {
        "provider": "groq",
        "model": "model-a",
        "state": "open",
        "last_failure": 30.0,
        "last_success": 5.0,
        "last_operation": "hrn_relational",
        "failures": 2,
        "consecutive_failures": 2,
        "cooldown_until": 90.0,
        "category": "provider_failure",
        "last_error": "read operation timed out",
    }

    health_store.merge_health_state(local, remote, now=31.0)

    assert local["last_operation"] == "hrn_relational"
    assert local["state"] == "open"


def test_equal_timestamp_failure_merge_uses_higher_consecutive_count_operation():
    local = {
        "provider": "groq",
        "model": "model-a",
        "state": "open",
        "last_failure": 30.0,
        "last_success": 5.0,
        "last_operation": "general_guide_composition",
        "failures": 2,
        "consecutive_failures": 1,
        "cooldown_until": 90.0,
    }
    remote = {
        "provider": "groq",
        "model": "model-a",
        "state": "open",
        "last_failure": 30.0,
        "last_success": 5.0,
        "last_operation": "hrn_relational",
        "failures": 3,
        "consecutive_failures": 2,
        "cooldown_until": 100.0,
        "category": "provider_failure",
        "last_error": "request timed out",
    }

    health_store.merge_health_state(local, remote, now=31.0)

    assert local["failures"] == 3
    assert local["consecutive_failures"] == 2
    assert local["last_operation"] == "hrn_relational"


def test_expired_remote_failure_cooldown_becomes_half_open():
    local = {
        "provider": "groq",
        "model": "model-a",
        "state": "open",
        "last_failure": 20.0,
        "last_success": 10.0,
        "failures": 1,
        "consecutive_failures": 1,
        "cooldown_until": 25.0,
        "quarantine_until": 0.0,
    }
    remote = {
        "provider": "groq",
        "model": "model-a",
        "state": "open",
        "last_failure": 20.0,
        "last_success": 10.0,
        "failures": 1,
        "consecutive_failures": 1,
        "cooldown_until": 25.0,
        "quarantine_until": 0.0,
    }

    health_store.merge_health_state(local, remote, now=30.0)

    assert local["state"] == "half_open"
    assert local["probe_in_flight"] is False


def test_quality_rejection_releases_half_open_transport_probe(monkeypatch):
    _reset_pending_persistence()
    state = provider_bank.new_state("groq", "model-a")
    state["state"] = "half_open"
    state["probe_in_flight"] = True
    monkeypatch.setattr(provider_bank, "_STATE", {
        "models": {"groq:model-a": state},
        "quality": {},
        "provider_cursor": 0,
        "model_cursors": {},
    })
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: None)

    provider_bank._record_quality_rejection(
        "groq", "model-a", "hrn_relational", "prescriptive-language"
    )

    assert state["probe_in_flight"] is False
    assert state["state"] == "half_open"


def test_remote_health_merge_cannot_overwrite_newer_local_failure(monkeypatch):
    _reset_pending_persistence()
    local = provider_bank.new_state("groq", "model-a")
    remote = {
        "groq:model-a": {
            "provider": "groq",
            "model": "model-a",
            "state": "open",
            "last_failure": 10.0,
            "last_success": 0.0,
            "failures": 1,
            "consecutive_failures": 1,
            "cooldown_until": 70.0,
            "quarantine_until": 0.0,
            "last_error": "stale remote failure",
            "category": "rate_limited",
            "last_operation": "old_operation",
        }
    }
    monkeypatch.setattr(provider_bank, "_STATE", {
        "models": {"groq:model-a": local},
        "quality": {},
        "provider_cursor": 0,
        "model_cursors": {},
    })
    monkeypatch.setattr(provider_bank, "load_remote_states", lambda: remote)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: None)
    failure = provider_bank.ProviderCallError(
        "newer local failure", "groq", "model-a", 429, category="rate_limited"
    )

    _run_two_state_transitions(
        provider_bank._sync_shared_state,
        lambda: provider_bank._failure(failure, "groq", "model-a", operation="new_operation"),
    )

    assert local["last_error"] == "newer local failure"
    assert local["last_operation"] == "new_operation"
    assert local["last_failure"] > 10.0


def test_concurrent_route_does_not_wait_for_another_health_flush(monkeypatch):
    _reset_pending_persistence()
    monkeypatch.setattr(provider_bank, "_STATE", {
        "models": {"groq:model-a": provider_bank.new_state("groq", "model-a")},
        "quality": {},
        "provider_cursor": 0,
        "model_cursors": {},
    })
    started = threading.Event()
    release = threading.Event()
    writes = []

    def save(states):
        writes.append(states)
        if len(writes) == 1:
            started.set()
            assert release.wait(timeout=2)
        return True

    monkeypatch.setattr(provider_bank, "save_remote_states", save)
    provider_bank._mark_shared_state_pending()
    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(provider_bank._flush_pending_shared_state)
        assert started.wait(timeout=1)
        # A concurrent route must return immediately and leave pending state intact.
        assert provider_bank._flush_pending_shared_state() is False
        provider_bank._mark_shared_state_pending()
        release.set()
        assert first.result(timeout=2) is True

    assert provider_bank._PENDING_SHARED_STATE is True
    assert provider_bank._flush_pending_shared_state() is True
    assert provider_bank._PENDING_SHARED_STATE is False
    assert len(writes) == 2


def test_shared_python_php_provider_health_merge_fixtures():
    fixture_path = Path(__file__).resolve().parents[1] / "QA" / "provider_health_merge_fixtures_v2.json"
    fixtures = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert fixtures["contract_version"] == "v2"

    for case in fixtures["cases"]:
        local = dict(case["local"])
        health_store.merge_health_state(local, case["remote"], now=case["now"])
        for field, expected in case["expected"].items():
            assert local.get(field) == expected, case["name"] + ":" + field


def test_provider_inventory_discovery_runs_outside_provider_state_lock(monkeypatch):
    _reset_pending_persistence()
    lock_acquired = threading.Event()

    class Core:
        def get_live_groq_models(self):
            # _configured invokes this from its discovery worker. It must be
            # able to acquire the state lock while discovery is in progress.
            with provider_bank._STATE_LOCK:
                lock_acquired.set()
            return ["model-a"]

    monkeypatch.setattr(provider_bank, "PRODUCTION_GROQ_MODELS", ["model-a"])
    monkeypatch.setattr(provider_bank, "_eligible", lambda *args, **kwargs: (True, []))
    monkeypatch.setattr(provider_bank, "_blocked_for_operation", lambda *args, **kwargs: False)
    monkeypatch.setattr(provider_bank, "_state", lambda *args, **kwargs: {
        "state": "healthy",
        "failures": 0,
        "consecutive_failures": 0,
        "last_success": 1.0,
    })
    monkeypatch.setattr(provider_bank, "_quality_state", lambda *args, **kwargs: {
        "quality_failures": 0,
        "quality_cooldown_until": 0.0,
    })
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    result = provider_bank.candidates(Core(), operation="generic")

    assert lock_acquired.is_set()
    assert len(result) == 1
    assert result[0]["model"] == "model-a"


def test_provider_inventory_discovery_runs_outside_snapshot_state_lock(monkeypatch):
    lock_acquired = threading.Event()

    class Core:
        def get_live_groq_models(self):
            with provider_bank._STATE_LOCK:
                lock_acquired.set()
            return ["model-a"]

    monkeypatch.setattr(provider_bank, "PRODUCTION_GROQ_MODELS", ["model-a"])
    monkeypatch.setattr(provider_bank, "_snapshot_from_configured", lambda configured: configured)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    result = provider_bank.snapshot(Core())

    assert lock_acquired.is_set()
    assert result == {"groq": ["model-a"]}


def test_stale_candidate_snapshot_rechecks_quality_cooldown_before_probe_claim(monkeypatch):
    _reset_pending_persistence()
    model = provider_bank.new_state("groq", "model-a")
    model["state"] = "half_open"
    model["probe_in_flight"] = False
    quality_key = provider_bank._quality_key("hrn_relational", "groq", "model-a")
    quality = {
        "provider": "groq",
        "model": "model-a",
        "operation": "hrn_relational",
        "quality_failures": 1,
        "last_quality_failure": 10.0,
        "last_quality_success": 0.0,
        "quality_cooldown_until": provider_bank.time.time() + 300.0,
        "quality_error": "prescriptive-language",
    }
    monkeypatch.setattr(provider_bank, "_STATE", {
        "models": {"groq:model-a": model},
        "quality": {quality_key: quality},
        "provider_cursor": 0,
        "model_cursors": {},
    })

    claimed_state, exclusion = provider_bank._claim_candidate(
        "groq", "model-a", "hrn_relational"
    )

    assert claimed_state is model
    assert exclusion == "quality"
    assert model["probe_in_flight"] is False
