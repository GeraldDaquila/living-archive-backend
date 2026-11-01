"""Provider-bank route batches shared health writes into one route-boundary snapshot."""
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
    monkeypatch.setattr(health_store, "_request", lambda *args, **kwargs: _ack(written=0))
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
    monkeypatch.setattr(health_health_store, "_READ_CACHE", None)
    monkeypatch.setattr(health_health_store, "_READ_CACHE_UNTIL", 0.0)
    monkeypatch.setattr(
        health_health_store,
        "_request",
        lambda method, payload=None: {"contract_version": "v1", "states": {}},
    )
    assert health_store.load_remote_states() is None
