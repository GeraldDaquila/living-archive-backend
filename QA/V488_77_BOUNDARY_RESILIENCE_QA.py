"""v488.77 boundary-resilience structural QA."""

from pathlib import Path
import ast
import time

ROOT = Path(__file__).resolve().parents[1]

def _source(path):
    return (ROOT / path).read_text(encoding="utf-8")

def main():
    resilience = _source("boundary_resilience.py")
    main_source = _source("main.py")
    hub = _source("hub_contracts.py")
    adapters = _source("specialist_adapters.py")

    ast.parse(resilience, filename="boundary_resilience.py")
    ast.parse(main_source, filename="main.py")
    ast.parse(hub, filename="hub_contracts.py")
    ast.parse(adapters, filename="specialist_adapters.py")

    assert 'CONTRACT_VERSION = "v1"' in resilience
    assert "class StaleAuthorityCache" in resilience
    assert "preserve_specialist_payload" in resilience
    assert "STALE" in resilience
    assert "UNAVAILABLE" in resilience

    assert 'APP_VERSION = "v489.14"' in main_source
    assert "boundary_resilience" in main_source
    assert "GUIDE_NODE_REGISTRY_FRESH_TTL_SECONDS" in main_source
    assert "GUIDE_NODE_REGISTRY_MAX_STALE_SECONDS" in main_source
    assert "guide_node_registry_state" in main_source

    # Stale authority must remain usable as data but must not be treated as fresh.
    import boundary_resilience as br
    clock = {"now": 100.0}
    original_time = br.time.time
    br.time.time = lambda: clock["now"]
    try:
        cache = br.StaleAuthorityCache(fresh_ttl_seconds=20, max_stale_seconds=60, failure_retry_seconds=10)
        calls = {"n": 0}
        def loader():
            calls["n"] += 1
            if calls["n"] == 1:
                return [{"node_id": "known-good"}]
            raise RuntimeError("temporary outage")
        value, state = cache.get(loader)
        assert value == [{"node_id": "known-good"}]
        assert state == br.FRESH
        clock["now"] = 130.0
        value, state = cache.get(loader)
        assert value == [{"node_id": "known-good"}]
        assert state == br.STALE
        assert cache.snapshot()["state"] == br.STALE
    finally:
        br.time.time = original_time

    # Payload preservation must be deep and lossless at the boundary.
    original = {"human_response": "Keep this exact sentence.", "journey": {"step": 1}}
    copied = br.preserve_specialist_payload(original, required_keys=("human_response",))
    assert copied == original
    copied["journey"]["step"] = 2
    assert original["journey"]["step"] == 1

    # The Hub must require the common contract and preserve domain payload.
    assert 'contract_version = str(contribution.get("contract_version") or "").strip()' in hub
    assert 'payload = contribution.get("payload")' in hub
    assert "preserve_specialist_payload" in adapters

    print("v488.77 boundary-resilience structural QA: PASS")

if __name__ == "__main__":
    main()
