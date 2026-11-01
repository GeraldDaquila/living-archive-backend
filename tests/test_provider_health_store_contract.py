"""Strict v2 acknowledgement tests for the shared provider-health bridge."""
import provider_health_store as store


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
        store,
        "_request",
        lambda method, payload=None: calls.append((method, payload)) or _ack(),
    )
    states = {"groq:model-a": {"provider": "groq"}, "nvidia:model-b": {"provider": "nvidia"}}

    assert store.save_remote_states(states) is True
    assert calls[0][0] == "POST"
    assert calls[0][1]["contract_version"] == "v2"
    assert calls[0][1]["states"] == states


def test_zero_write_acknowledgement_is_rejected(monkeypatch):
    monkeypatch.setattr(store, "_request", lambda *args, **kwargs: _ack(written=0))
    assert store.save_remote_states({"groq:model-a": {}}) is False


def test_partial_write_acknowledgement_is_rejected(monkeypatch):
    monkeypatch.setattr(store, "_request", lambda *args, **kwargs: _ack(written=1))
    assert store.save_remote_states({"groq:model-a": {}, "nvidia:model-b": {}}) is False


def test_missing_or_wrong_contract_version_is_rejected(monkeypatch):
    monkeypatch.setattr(store, "_request", lambda *args, **kwargs: {"success": True, "submitted": 2, "written": 2})
    assert store.save_remote_states({"groq:model-a": {}, "nvidia:model-b": {}}) is False

    monkeypatch.setattr(store, "_request", lambda *args, **kwargs: _ack(version="v1"))
    assert store.save_remote_states({"groq:model-a": {}, "nvidia:model-b": {}}) is False


def test_missing_or_false_success_is_rejected(monkeypatch):
    monkeypatch.setattr(store, "_request", lambda *args, **kwargs: {"contract_version": "v2", "submitted": 2, "written": 2})
    assert store.save_remote_states({"groq:model-a": {}, "nvidia:model-b": {}}) is False

    monkeypatch.setattr(store, "_request", lambda *args, **kwargs: _ack(success=False))
    assert store.save_remote_states({"groq:model-a": {}, "nvidia:model-b": {}}) is False


def test_boolean_counts_are_rejected(monkeypatch):
    monkeypatch.setattr(store, "_request", lambda *args, **kwargs: _ack(submitted=True, written=True))
    assert store.save_remote_states({"groq:model-a": {}, "nvidia:model-b": {}}) is False


def test_mismatched_submitted_count_is_rejected(monkeypatch):
    monkeypatch.setattr(store, "_request", lambda *args, **kwargs: _ack(submitted=1, written=2))
    assert store.save_remote_states({"groq:model-a": {}, "nvidia:model-b": {}}) is False


def test_behavioral_last_operation_is_exported():
    state = {
        "provider": "groq",
        "model": "model-a",
        "last_operation": "hrn_relational",
        "probe_successes": 7,
        "probe_in_flight": True,
    }
    exported = store.export_health_states({"groq:model-a": state})["groq:model-a"]

    assert exported["last_operation"] == "hrn_relational"
    assert "probe_successes" not in exported
    assert exported["probe_in_flight"] is False
