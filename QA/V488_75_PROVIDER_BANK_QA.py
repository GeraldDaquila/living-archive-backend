"""v488.77 provider-resilience structural and behavioral QA."""
from pathlib import Path
from unittest.mock import patch
import ast
import os
import re
import provider_bank

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

    # OpenRouter is an optional, zero-cost fallback lane. Verify it is enabled
    # only by an explicit key and that its router-level capabilities admit HRN.
    assert '"OPENROUTER_API_KEY"' in provider
    assert '"openrouter/free"' in provider
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key", "USE_OPENROUTER_MODELS": ""}, clear=False):
        configured = provider_bank._configured(None)
        assert configured.get("openrouter") == [
            "openrouter/free",
            "nvidia/nemotron-3-ultra-550b-a55b:free",
            "google/gemma-4-31b-it:free",
        ]
        eligible, missing = provider_bank._eligible("openrouter", "openrouter/free", "hrn_relational")
        assert eligible, f"OpenRouter free router lacks HRN capability: {missing}"

    # A configured OpenRouter lane must be selected before the other providers.
    # This protects it from being starved by the bank's bounded attempt window.
    with (
        patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key", "USE_LLM_PROVIDER_ORDER": "groq,gemini,mistral,workers_ai"}, clear=False),
        patch.object(provider_bank, "_STATE", {"models": {}, "provider_cursor": 0, "model_cursors": {}}),
        patch.object(provider_bank, "candidates", return_value=[
            {"provider": "groq", "model": "openai/gpt-oss-120b", "index": 0},
            {"provider": "groq", "model": "openai/gpt-oss-20b", "index": 1},
            {"provider": "openrouter", "model": "openrouter/free", "index": 0},
            {"provider": "openrouter", "model": "nvidia/nemotron-3-ultra-550b-a55b:free", "index": 1},
            {"provider": "openrouter", "model": "google/gemma-4-31b-it:free", "index": 2},
            {"provider": "gemini", "model": "gemini-3.8-flash", "index": 0},
        ]),
    ):
        selected = provider_bank.select(None, operation="hrn_relational")
        assert [item["provider"] for item in selected[:3]] == ["openrouter", "openrouter", "openrouter"]

    version_match = re.search(r'APP_VERSION = "(v[0-9.]+)"', main_source)
    assert version_match, "APP_VERSION missing"
    app_version = version_match.group(1)
    assert f'if str(APP_VERSION) != "{app_version}":' in main_source
    assert f'DEPLOYMENT_FINGERPRINT = "USE-{app_version}-' in main_source
    assert f'CANONICAL_BUILD_ID = "USE-BUILD-{app_version}-' in main_source

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

    print("v488.77 provider-resilience structural and behavioral QA: PASS")

if __name__ == "__main__":
    main()
