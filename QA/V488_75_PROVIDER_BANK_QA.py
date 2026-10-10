"""v488.77 provider-resilience structural and behavioral QA."""
from pathlib import Path
from unittest.mock import patch
import ast
import json
import time
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

    # HRN's multiple semantic stages must not each fan out across the entire bank.
    # Two candidate attempts per HRN stage preserve an independent fallback while
    # bounding nested latency; non-HRN operations retain the configured cap.
    assert 'hrn_operations = {"hrn_perception", "hrn_relational", "hrn_voice_repair"}' in provider
    assert "operation_attempt_cap = 2 if operation in hrn_operations else configured_attempts" in provider
    assert "max_attempts = min(len(pool), operation_attempt_cap)" in provider
    # HRN stages share one visitor turn: provider priority must not rotate between
    # perception and composition, or the bounded window can skip a healthy primary.
    assert 'if operation not in {"hrn_perception", "hrn_relational", "hrn_voice_repair"}:' in provider
    assert 'providers = _rotate(providers, int(_STATE["provider_cursor"]))' in provider
    # Bound latency-heavy visitor-facing prose stages without truncating the
    # richer perception/Observer schema needed to form the relational fractal.
    assert '"hrn_relational": 600' in provider
    assert 'requested_max_tokens = min(requested_max_tokens, 600)' in provider
    assert 'if operation in {"hrn_relational", "hrn_voice_repair"}:' in provider
    # Slow Workers AI models must not consume the full generic timeout on every
    # HRN stage or on the bounded contract-correction call.
    assert 'timeout_override=8 if operation in hrn_operations else None' in provider
    assert 'timeout=timeout_override or 12' in provider

    # A rejected HRN visitor-surface response must receive explicit, phrase-aware
    # correction guidance rather than a schema-only retry that repeats the same voice.
    recovery_start = provider.index("recovery_messages.append({")
    recovery_end = provider.index("recovered = parse", recovery_start)
    recovery_prompt = provider[recovery_start:recovery_end]
    for phrase in (
        "Do not repeat the rejected wording",
        "this distinction matters because",
        "Avoid generic relationship theory",
        "Use one concrete observation grounded in the visitor's actual words",
        "Do not restate the same insight in new words",
    ):
        assert phrase in recovery_prompt, f"HRN contract-recovery guidance missing: {phrase}"

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
        selected_providers = [item["provider"] for item in selected]
        assert selected_providers[0] == "openrouter"
        assert selected_providers[1] == "groq", "HRN's second bounded attempt must be an independent provider"
        # Stable lane priority must persist across semantic stages.
        selected_again = provider_bank.select(None, operation="hrn_perception")
        assert [item["provider"] for item in selected_again[:2]] == ["openrouter", "groq"]

    # Invalid JSON from a provider must be recorded as a transient provider
    # health failure, not upgraded to a permanent structured-output quarantine.
    valid_hrn = json.dumps({
        "response": "You describe doing most of the repair work, while the other person's intentions remain unknown.",
        "question": "What part of the effort has felt most one-sided to you?",
    })
    pool = [
        {"provider": "openrouter", "model": "openrouter/free", "index": 0},
        {"provider": "groq", "model": "openai/gpt-oss-120b", "index": 0},
    ]
    with (
        patch.object(provider_bank, "select", return_value=pool),
        patch.object(provider_bank, "_call", side_effect=["not-json", valid_hrn]),
        patch.object(provider_bank, "_STATE", {"models": {}, "provider_cursor": 0, "model_cursors": {}}),
        patch.object(provider_bank, "acquire_probe", return_value=True),
        patch.object(provider_bank, "_success"),
    ):
        routed = provider_bank.route(
            use_core=None,
            messages=[{"role": "user", "content": "I am doing most of the repair work."}],
            max_tokens=600,
            parse=json.loads,
            operation="hrn_relational",
        )
        failed_state = provider_bank._STATE["models"]["openrouter:openrouter/free"]
    assert routed["provider"] == "groq"
    assert failed_state["category"] == "invalid_provider_response"
    assert failed_state["quarantine_until"] == 0.0
    assert failed_state["cooldown_until"] > 0.0

    # OpenRouter's free daily allowance is shared across model IDs. A 429
    # for free-models-per-day must quarantine the whole OpenRouter lane until
    # the provider-supplied reset timestamp, rather than retrying siblings.
    reset_ms = int((time.time() + 7200) * 1000)
    with patch.object(provider_bank, "_STATE", {"models": {
        "openrouter:openrouter/free": provider_bank.new_state("openrouter", "openrouter/free"),
        "openrouter:nvidia/nemotron-3-ultra-550b-a55b:free": provider_bank.new_state(
            "openrouter", "nvidia/nemotron-3-ultra-550b-a55b:free"
        ),
    }, "provider_cursor": 0, "model_cursors": {}}):
        daily_quota_error = provider_bank.ProviderCallError(
            "HTTP 429: Rate limit exceeded: free-models-per-day. "
            + '"X-RateLimit-Reset":"' + str(reset_ms) + '"',
            "openrouter", "openrouter/free", status_code=429,
        )
        provider_bank._failure(daily_quota_error, "openrouter", "openrouter/free")
        router_state = provider_bank._STATE["models"]["openrouter:openrouter/free"]
        sibling_state = provider_bank._STATE["models"]["openrouter:nvidia/nemotron-3-ultra-550b-a55b:free"]
    assert router_state["category"] == "free_tier_daily_quota"
    assert sibling_state["category"] == "free_tier_daily_quota"
    assert router_state["quarantine_until"] > time.time() + 7100
    assert sibling_state["quarantine_until"] > time.time() + 7100

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

    # P0 durable shared-state regression suite is part of the existing release gate.
    import unittest
    import test_provider_health_store
    store_source = _source("provider_health_store.py")
    ast.parse(store_source, filename="provider_health_store.py")
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_provider_health_store)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful(), "shared provider health-state tests failed"

    print("v488.77 provider-resilience structural and behavioral QA: PASS")

if __name__ == "__main__":
    main()
