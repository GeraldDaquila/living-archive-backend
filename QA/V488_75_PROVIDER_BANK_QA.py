"""v488.77 provider-resilience structural and behavioral QA."""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]

def _source(path):
    return (ROOT / path).read_text(encoding="utf-8")

def main():
    resilience = _source("provider_resilience.py")
    provider = _source("provider_bank.py")
    main_source = _source("main.py")

    ast.parse(resilience, filename="provider_resilience.py")
    ast.parse(provider, filename="provider_bank.py")
    ast.parse(main_source, filename="main.py")

    assert 'CONTRACT_VERSION = "v1"' in resilience
    for marker in ("HEALTHY", "DEGRADED", "OPEN", "HALF_OPEN"):
        assert marker in resilience
    assert "def blocked(" in resilience
    assert "def acquire_probe(" in resilience
    assert "def record_failure(" in resilience
    assert "def record_success(" in resilience
    assert "def aggregate_provider_health(" in resilience

    assert "provider_resilience" in provider
    assert "record_failure(" in provider
    assert "record_success(" in provider
    assert "acquire_probe(" in provider
    assert '"gemini-2.5-flash"' not in provider
    assert '["gemini-3.8-flash"]' in provider
    assert 'CONTRACT_VERSION = "v2"' in provider

    gemini_start = provider.index("def _gemini(")
    gemini_end = provider.index("\ndef _openai_compatible", gemini_start)
    gemini = provider[gemini_start:gemini_end]
    assert '"maxOutputTokens": max_tokens' in gemini
    assert 'payload["generationConfig"]["responseMimeType"] = "application/json"' in gemini
    assert '"thinkingConfig": {"thinkingLevel": "low"}' in gemini
    assert '"temperature": 0.0' not in gemini

    assert 'APP_VERSION = "v489.13"' in main_source
    assert 'DEPLOYMENT_FINGERPRINT = "USE-v489.13-general-answer-recovery"' in main_source
    assert 'CANONICAL_BUILD_ID = "USE-BUILD-v489.13-general-answer-recovery"' in main_source

    # Behavioral self-healing check:
    # failure -> open -> cooldown expiry -> one recovery probe -> healthy.
    import provider_resilience as pr
    state = pr.new_state("test", "model")
    pr.record_failure(state, "rate_limited", "429", now=100.0, retry_after=10.0)
    assert state["state"] == pr.OPEN
    assert pr.blocked(state, now=105.0) is True
    assert pr.blocked(state, now=131.0) is False
    assert state["state"] == pr.HALF_OPEN
    assert pr.acquire_probe(state) is True
    assert pr.acquire_probe(state) is False
    pr.record_success(state, now=132.0)
    assert state["state"] == pr.HEALTHY
    assert state["consecutive_failures"] == 0

    print("v488.76 provider-resilience structural and behavioral QA: PASS")

if __name__ == "__main__":
    main()
