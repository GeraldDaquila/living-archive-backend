"""Regression tests for the advisory provider-health bridge circuit breaker."""
import json
from types import SimpleNamespace
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
        def __init__(self):
            self.body = json.dumps({"contract_version": store.CONTRACT_VERSION, "states": {}}).encode()
            self.fp = SimpleNamespace(raw=SimpleNamespace(_sock=SimpleNamespace(settimeout=lambda value: None)))

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read1(self, _limit):
            body, self.body = self.body, b""
            return body

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


def test_normal_requests_are_not_marked_as_half_open_probes(monkeypatch):
    _reset_circuit()

    class Response:
        def __init__(self):
            self.body = json.dumps({"contract_version": store.CONTRACT_VERSION, "states": {}}).encode()
            self.fp = SimpleNamespace(raw=SimpleNamespace(_sock=SimpleNamespace(settimeout=lambda value: None)))

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read1(self, _limit):
            body, self.body = self.body, b""
            return body

    monkeypatch.setenv("USE_PROVIDER_BANK_SHARED_SECRET", "test-secret")
    monkeypatch.setattr(store, "urlopen", lambda *args, **kwargs: Response())
    assert store._request("GET") == {"contract_version": store.CONTRACT_VERSION, "states": {}}
    assert store._CIRCUIT_PROBE_IN_FLIGHT is False
    assert store._CIRCUIT_OPEN_UNTIL == 0.0



def test_late_v2_transport_result_reaches_background_ack_handler(monkeypatch):
    import threading
    import time

    _reset_circuit()
    monkeypatch.setattr(store, "_configuration", lambda: ("https://health.invalid/state", "test-secret"))
    monkeypatch.setattr(store, "TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(store, "urlopen", lambda *args, **kwargs: object())
    body = b'{"contract_version":"v2","success":true,"submitted":1,"written":1}'

    def delayed_body(*args, **kwargs):
        time.sleep(0.04)
        return body

    monkeypatch.setattr(store, "_read_response_body", delayed_body)
    received = threading.Event()
    result = store._request(
        "POST",
        {"contract_version": "v2", "states": {"groq:model-a": {}}},
        on_late_result=lambda value: received.set() if value.get("written") == 1 else None,
    )
    assert result is None
    assert received.wait(0.5)
