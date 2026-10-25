"""Regression tests for the advisory provider-health bridge circuit breaker."""
import json
from urllib.error import URLError

import provider_health_store as store


def _reset_circuit():
    store._CIRCUIT_OPEN_UNTIL = 0.0
    store._CIRCUIT_PROBE_IN_FLIGHT = False


def test_failed_shared_health_probe_opens_short_circuit(monkeypatch):
    _reset_circuit()
    calls = []

    def fail(*args, **kwargs):
        calls.append((args, kwargs))
        raise URLError("simulated unavailable bridge")

    monkeypatch.setenv("USE_PROVIDER_BANK_SHARED_SECRET", "test-secret")
    monkeypatch.setattr(store, "urlopen", fail)
    assert store._request("GET") is None
    assert store._CIRCUIT_OPEN_UNTIL > store.time.monotonic()
    assert store._request("POST", {"states": {}}) is None
    assert len(calls) == 1
    assert store._CIRCUIT_PROBE_IN_FLIGHT is False


def test_successful_probe_closes_circuit(monkeypatch):
    _reset_circuit()
    calls = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, _limit):
            return json.dumps({"contract_version": store.CONTRACT_VERSION, "states": {}}).encode()

    def succeed(*args, **kwargs):
        calls.append((args, kwargs))
        return Response()

    monkeypatch.setenv("USE_PROVIDER_BANK_SHARED_SECRET", "test-secret")
    monkeypatch.setattr(store, "urlopen", succeed)
    assert store._request("GET") == {"contract_version": store.CONTRACT_VERSION, "states": {}}
    assert store._CIRCUIT_OPEN_UNTIL == 0.0
    assert store._CIRCUIT_PROBE_IN_FLIGHT is False
    assert len(calls) == 1


def test_circuit_does_not_open_when_shared_store_is_unconfigured(monkeypatch):
    _reset_circuit()
    monkeypatch.delenv("USE_PROVIDER_BANK_SHARED_SECRET", raising=False)
    monkeypatch.delenv("USE_PROVIDER_HEALTH_STATE_URL", raising=False)
    assert store._request("GET") is None
    assert store._CIRCUIT_OPEN_UNTIL == 0.0
