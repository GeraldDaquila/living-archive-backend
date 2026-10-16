"""v489.79 provider resilience and NVIDIA non-thinking recovery QA."""
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

    # If Groq inference credentials exist but model inventory discovery is
    # temporarily empty, retain the documented catalog for normal health-gated
    # attempts instead of silently removing the entire provider lane.
    fake_groq_core = type("FakeGroqCore", (), {"get_live_groq_models": lambda self: []})()
    with (
        patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}, clear=False),
        patch.object(provider_bank, "PRODUCTION_GROQ_MODELS", ["openai/gpt-oss-120b"]),
    ):
        configured = provider_bank._configured(fake_groq_core)
        assert configured.get("groq") == ["openai/gpt-oss-120b"]

    # A hung inventory endpoint must not block the provider-bank request path.
    slow_groq_core = type(
        "SlowGroqCore",
        (),
        {"get_live_groq_models": lambda self: (provider_bank.time.sleep(0.5), [])[1]},
    )()
    with (
        patch.dict(os.environ, {
            "GROQ_API_KEY": "test-key",
            "USE_GROQ_INVENTORY_TIMEOUT_SECONDS": "0.1",
        }, clear=False),
        patch.object(provider_bank, "PRODUCTION_GROQ_MODELS", ["openai/gpt-oss-120b"]),
    ):
        started = provider_bank.time.monotonic()
        configured = provider_bank._configured(slow_groq_core)
        elapsed = provider_bank.time.monotonic() - started
        assert elapsed < 0.4, f"Groq inventory discovery blocked the request path for {elapsed:.2f}s"
        assert configured.get("groq") == ["openai/gpt-oss-120b"]

    # HRN's multiple semantic stages must not each fan out across the entire bank.
    # One candidate per primary gateway request leaves the WordPress bridge's
    # bounded mirror replay as the independent fallback; diagnostics may opt into two.
    assert 'hrn_operations = {"hrn_perception", "hrn_relational", "hrn_voice_repair"}' in provider
    assert "def _hrn_attempt_cap():" in provider
    assert 'os.getenv("USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS", "1")' in provider
    assert "if operation in hrn_operations:" in provider
    assert "elif bounded_guide_operation:" in provider
    assert "operation_attempt_cap = 1" in provider
    assert "GENERAL_GUIDE_FAST_FAILURE_WINDOW_SECONDS = 5.0" in provider
    assert "GENERAL_GUIDE_FAST_FALLBACK_MAX_CANDIDATES = 3" in provider
    assert "GENERAL_GUIDE_PROVIDER_CALL_TIMEOUT_SECONDS = 1.5" in provider
    assert "base_max_attempts = min(len(pool), operation_attempt_cap)" in provider
    assert "HRN_RELATIONAL_FAST_FAILURE_WINDOW_SECONDS = 4.5" in provider
    assert "action=try_independent_candidate" in provider
    assert "action=skip_extra_candidate" in provider
    assert '0 if "low_latency" in (item.get("capabilities") or []) else 1' in provider
    # HRN stages share one visitor turn: provider priority must not rotate between
    # perception and composition, or the bounded window can skip a healthy primary.
    assert 'if operation not in {"hrn_perception", "hrn_relational", "hrn_voice_repair"}:' in provider
    assert 'providers = _rotate(providers, int(_STATE["provider_cursor"]))' in provider
    # Bound latency-heavy visitor-facing prose stages without truncating the
    # richer perception/Observer schema needed to form the relational fractal.
    assert '"hrn_relational": 600' in provider
    assert 'requested_max_tokens = min(requested_max_tokens, HRN_RELATIONAL_MAX_COMPLETION_TOKENS)' in provider
    assert 'if operation in {"hrn_relational", "hrn_voice_repair"}:' in provider
    # Provider-specific HRN transport budgets stay bounded; the proven Gemma
    # 4 26B lane gets a narrowly scoped 2.5-second timeout exception.
    assert "candidate_timeout = _provider_call_timeout(operation, item) or 0.0" in provider
    assert "timeout_override=_provider_call_timeout(operation, item)" in provider
    assert 'HRN_PROVIDER_CALL_TIMEOUT_SECONDS = 1.5' in provider
    assert 'HRN_GEMMA_4_26B_PROVIDER_CALL_TIMEOUT_SECONDS = 2.5' in provider
    assert 'model == "@cf/google/gemma-4-26b-a4b-it"' in provider
    assert 'timeout = max(1.0, min(10.0, float(timeout)))' in provider
    assert 'timeout=timeout_override or 12' in provider
    # The visitor contract must explicitly block inferred blame and motive attribution,
    # not merely generic relationship theory or advice.
    visitor_contract_start = provider.index("def _apply_hrn_visitor_contract")
    visitor_contract_end = provider.index("def _apply_hrn_voice_repair_contract", visitor_contract_start)
    visitor_contract = provider[visitor_contract_start:visitor_contract_end]
    for phrase in (
        "not turn the visitor's feeling of being",
        "a verdict about the other person's character or intent",
        "avoiding accountability, refusing to listen",
        "without inferring motive",
    ):
        assert phrase in visitor_contract, f"HRN inferred-intent guard missing: {phrase}"

    # A rejected HRN visitor-surface response must receive explicit, phrase-aware
    # correction guidance rather than a schema-only retry that repeats the same voice.
    recovery_start = provider.index("correction_content = (")
    recovery_end = provider.index('if operation == "hrn_relational":', recovery_start)
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
        strict_schema = {"strict": True, "schema": {"type": "object", "properties": {"response": {"type": "string"}}}}
        eligible, missing = provider_bank._eligible(
            "openrouter", "openrouter/free", "hrn_relational", schema=strict_schema
        )
        assert eligible, (
            "HRN relational must retain JSON-object-capable providers when strict-schema "
            f"format is unavailable and provider-neutral fallback is supported: {missing}"
        )

    # A configured OpenRouter lane must be selected before the other providers.
    # This protects it from being starved by the bank's bounded attempt window.
    with (
        patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key", "USE_LLM_PROVIDER_ORDER": "groq,gemini,mistral,workers_ai,openrouter"}, clear=False),
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

    # For relational composition, operation-specific contract history outranks
    # general transport health from another specialist stage.
    with (
        patch.dict(os.environ, {"OPENROUTER_API_KEY": "", "USE_LLM_PROVIDER_ORDER": "nvidia,groq"}, clear=False),
        patch.object(provider_bank, "_STATE", {"models": {}, "provider_cursor": 0, "model_cursors": {}, "quality": {}}),
        patch.object(provider_bank, "candidates", return_value=[
            {"provider": "nvidia", "model": "nvidia/nemotron-3-super-120b-a12b", "index": 0, "health_state": "healthy", "quality_failures": 3, "consecutive_failures": 0, "transport_failures": 0, "last_success": 999},
            {"provider": "groq", "model": "openai/gpt-oss-120b", "index": 0, "health_state": "unknown", "quality_failures": 0, "consecutive_failures": 0, "transport_failures": 0, "last_success": 0},
        ]),
    ):
        relational_order = provider_bank.select(None, operation="hrn_relational")
        assert relational_order[0]["provider"] == "groq", (
            "A relational model with repeated contract rejections must not outrank "
            "a clean independent lane just because another operation marked it healthy."
        )
        perception_order = provider_bank.select(None, operation="hrn_perception")
        assert perception_order[0]["provider"] == "nvidia", (
            "The relational quality override must remain scoped to relational composition."
        )

    # HRN model arbitration must carry recent success across semantic stages.
    # A model that just succeeded in perception should outrank a sibling whose
    # quota health is stale, without disturbing provider-lane interleaving.
    with (
        patch.dict(os.environ, {"USE_LLM_PROVIDER_ORDER": "groq,gemini,mistral,workers_ai"}, clear=False),
        patch.object(provider_bank, "_STATE", {"models": {}, "provider_cursor": 0, "model_cursors": {}}),
        patch.object(provider_bank, "candidates", return_value=[
            {"provider": "groq", "model": "openai/gpt-oss-120b", "index": 0, "quality_failures": 0, "last_success": 10.0},
            {"provider": "groq", "model": "qwen/qwen3.8-27b", "index": 1, "quality_failures": 0, "last_success": 99.0},
            {"provider": "gemini", "model": "gemini-3.8-flash", "index": 0, "quality_failures": 0, "last_success": 20.0},
        ]),
    ):
        recent = provider_bank.select(None, operation="hrn_relational")
        assert recent[0]["provider"] == "groq"
        assert recent[0]["model"] == "qwen/qwen3.8-27b", "HRN should prefer the model that most recently succeeded"
        assert recent[1]["provider"] == "gemini", "Independent provider fallback remains second"

    # Health-aware HRN arbitration: a currently healthy model with prior
    # successful contract completions must outrank half-open models whose
    # transport history is stale, even if those models have fewer quality rejections.
    with (
        patch.dict(os.environ, {"USE_LLM_PROVIDER_ORDER": "workers_ai,groq,gemini,mistral"}, clear=False),
        patch.object(provider_bank, "_STATE", {"models": {}, "provider_cursor": 0, "model_cursors": {}}),
        patch.object(provider_bank, "candidates", return_value=[
            {"provider": "workers_ai", "model": "@cf/google/gemma-4-26b-a4b-it", "index": 0,
             "health_state": "healthy", "quality_failures": 2, "transport_failures": 0,
             "consecutive_failures": 0, "last_success": 80.0},
            {"provider": "workers_ai", "model": "@cf/meta/llama-3.3-70b-instruct-fp8-fast", "index": 1,
             "health_state": "open", "quality_failures": 0, "transport_failures": 3,
             "consecutive_failures": 2, "last_success": 0.0},
            {"provider": "groq", "model": "openai/gpt-oss-120b", "index": 0,
             "health_state": "healthy", "quality_failures": 0, "transport_failures": 0,
             "consecutive_failures": 0, "last_success": 90.0},
        ]),
    ):
        health_selected = provider_bank.select(None, operation="hrn_perception")
        assert health_selected[0]["provider"] == "workers_ai"
        assert health_selected[0]["model"] == "@cf/google/gemma-4-26b-a4b-it", (
            "Healthy, previously successful model must outrank half-open transport failures"
        )
        assert health_selected[1]["provider"] == "groq", (
            "Bounded HRN fallback must remain an independent provider"
        )

    # Invalid JSON from a provider must be recorded as a transient provider
    # health failure, not upgraded to a permanent structured-output quarantine.
    valid_hrn = json.dumps({
        "response": "You describe doing most of the repair work, while the other person's intentions remain unknown. That gap can make the effort feel one-sided without proving what the other person means to do.",
        "question": "What part of the effort has felt most one-sided to you?",
    })
    pool = [
        {"provider": "openrouter", "model": "openrouter/free", "index": 0},
        {"provider": "groq", "model": "openai/gpt-oss-120b", "index": 0},
    ]
    with (
        patch.dict(os.environ, {"USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS": "2"}, clear=False),
        patch.object(provider_bank, "select", return_value=pool),
        patch.object(provider_bank, "_call", side_effect=["not-json", valid_hrn]),
        patch.object(provider_bank, "_STATE", {"models": {}, "provider_cursor": 0, "model_cursors": {}}),
        patch.object(provider_bank, "acquire_probe", return_value=True),
        patch.object(provider_bank, "_success"),
    ):
        routed = provider_bank.route(
            use_core=None,
            messages=[{
                "role": "user",
                "content": (
                    "STRUCTURED MOVEMENT BRIEF\\n"
                    + json.dumps({
                        "working_hypothesis": "visitor is doing most of the repair work",
                        "thread_summary": "the repair effort feels one-sided",
                        "underlying_need": "understand which part of the repair effort feels one-sided",
                        "body_of_thought": "most of the repair work falls to the visitor",
                    })
                ),
            }],
            max_tokens=600,
            parse=json.loads,
            operation="hrn_relational",
        )
        failed_state = provider_bank._STATE["models"]["openrouter:openrouter/free"]
    assert routed["provider"] == "groq"
    assert failed_state["category"] == "invalid_provider_response"
    assert failed_state["quarantine_until"] == 0.0
    assert failed_state["cooldown_until"] > 0.0

    # Exercise the real Provider Bank route: semantic rejection must skip the
    # same-model correction request and continue to an independent valid provider.
    rejected_hrn = json.dumps({
        "response": "You are dealing with a friend who is avoiding accountability and refusing to listen. This clearly shows that they do not respect your feelings.",
        "question": "What happens just before you begin to feel unheard?",
    })
    independent_hrn = json.dumps({
        "response": "You described trying to explain your view and feeling unheard when disagreement starts. The impact on you is clear, even though your friend's reasons for responding that way are not yet known.",
        "question": "What happens just before you begin to feel unheard?",
    })
    pool = [
        {"provider": "nvidia", "model": "nvidia/nemotron-test", "index": 0},
        {"provider": "mistral", "model": "mistral-small-test", "index": 0},
    ]
    quality_events = []
    original_record_quality = provider_bank._record_quality_rejection
    def capture_quality(provider, model, operation, reason):
        quality_events.append((provider, model, operation, reason))
        return original_record_quality(provider, model, operation, reason)
    with (
        patch.dict(os.environ, {
            "USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS": "1",
            "USE_PROVIDER_BANK_MAX_ATTEMPTS": "2",
        }, clear=False),
        patch.object(provider_bank, "select", return_value=pool),
        patch.object(provider_bank, "_call", side_effect=[rejected_hrn, independent_hrn]) as model_call,
        patch.object(provider_bank, "_STATE", {"models": {}, "provider_cursor": 0, "model_cursors": {}, "quality": {}}),
        patch.object(provider_bank, "acquire_probe", return_value=True),
        patch.object(provider_bank, "_success"),
        patch.object(provider_bank, "_record_quality_rejection", side_effect=capture_quality),
    ):
        routed = provider_bank.route(
            use_core=None,
            messages=[{
                "role": "user",
                "content": "STRUCTURED MOVEMENT BRIEF\\n" + json.dumps({
                    "working_hypothesis": "visitor feels unheard when they disagree while doing most repair work",
                    "thread_summary": "repair effort feels one-sided and disagreement leaves the visitor feeling unheard",
                    "underlying_need": "understand what happens before feeling unheard and which repair work feels one-sided",
                    "body_of_thought": "disagreement, feeling unheard, and one-sided repair work are connected while motives remain unknown",
                }),
            }],
            max_tokens=600,
            parse=json.loads,
            operation="hrn_relational",
        )
    assert routed["provider"] == "mistral", "Rejected HRN voice must advance to independent provider."
    assert model_call.call_count == 2, "The rejected NVIDIA model must not receive a same-model correction call."
    assert quality_events and quality_events[0][0:3] == (
        "nvidia", "nvidia/nemotron-test", "hrn_relational"
    ), "Semantic rejection must be recorded as provider/model quality failure."
    assert provider_bank._hrn_surface_language_violation(routed["parsed"]["response"]) == "", (
        "Independent fallback must satisfy the unchanged visitor language policy."
    )

    # Missing or prescriptive questions are model-quality failures too.
    # The live HRN bridge rejects an empty question, so it must never receive a
    # transport-successful response that relies on a repair path it does not run.
    missing_question_hrn = json.dumps({
        "response": json.loads(valid_hrn)["response"],
        "question": "",
    })
    question_pool = [
        {"provider": "nvidia", "model": "nvidia/nemotron-missing-question-test", "index": 0},
        {"provider": "mistral", "model": "mistral-question-fallback-test", "index": 0},
    ]
    missing_question_events = []
    original_quality_recorder = provider_bank._record_quality_rejection
    def capture_missing_question_quality(provider, model, operation, reason):
        missing_question_events.append((provider, model, operation, reason))
        return original_quality_recorder(provider, model, operation, reason)
    with (
        patch.dict(os.environ, {
            "USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS": "1",
            "USE_PROVIDER_BANK_MAX_ATTEMPTS": "2",
        }, clear=False),
        patch.object(provider_bank, "select", return_value=question_pool),
        patch.object(provider_bank, "_call", side_effect=[missing_question_hrn, valid_hrn]) as question_call,
        patch.object(provider_bank, "_STATE", {"models": {}, "provider_cursor": 0, "model_cursors": {}, "quality": {}}),
        patch.object(provider_bank, "acquire_probe", return_value=True),
        patch.object(provider_bank, "_success"),
        patch.object(provider_bank, "_record_quality_rejection", side_effect=capture_missing_question_quality),
    ):
        question_routed = provider_bank.route(
            use_core=None,
            messages=[{
                "role": "user",
                "content": "STRUCTURED MOVEMENT BRIEF\\n" + json.dumps({
                    "working_hypothesis": "visitor feels unheard when they disagree while doing most repair work",
                    "thread_summary": "repair effort feels one-sided and disagreement leaves the visitor feeling unheard",
                    "underlying_need": "understand what happens before feeling unheard and which repair work feels one-sided",
                    "body_of_thought": "disagreement, feeling unheard, and one-sided repair work are connected while motives remain unknown",
                }),
            }],
            max_tokens=600,
            parse=json.loads,
            operation="hrn_relational",
        )
    assert question_routed["provider"] == "nvidia", (
        "A grounded movement brief should permit local question completion before another provider call."
    )
    assert question_call.call_count == 1, "Grounded local completion should not spend a second provider call."
    assert question_routed["parsed"]["question"].strip(), "The provider-bank result must carry a non-empty grounded question."
    assert "unheard" in question_routed["parsed"]["question"].casefold(), (
        "The locally completed question must retain the visitor-grounded relational subject."
    )
    assert not missing_question_events, "A successfully completed question must not be recorded as a quality rejection."

    # A short response is a field-level shape defect: permit one bounded
    # correction on the same candidate, then validate the corrected object.
    short_hrn = json.dumps({
        "response": "You feel unheard when disagreement starts.",
        "question": "What happens just before you feel unheard?",
    })
    shape_pool = [
        {"provider": "nvidia", "model": "nvidia/nemotron-shape-test", "index": 0},
    ]
    with (
        patch.dict(os.environ, {
            "USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS": "1",
            "USE_PROVIDER_BANK_MAX_ATTEMPTS": "1",
        }, clear=False),
        patch.object(provider_bank, "select", return_value=shape_pool),
        patch.object(provider_bank, "_call", side_effect=[short_hrn, independent_hrn]) as shape_call,
        patch.object(provider_bank, "_STATE", {"models": {}, "provider_cursor": 0, "model_cursors": {}, "quality": {}}),
        patch.object(provider_bank, "acquire_probe", return_value=True),
        patch.object(provider_bank, "_success"),
    ):
        shape_routed = provider_bank.route(
            use_core=None,
            messages=[{
                "role": "user",
                "content": "STRUCTURED MOVEMENT BRIEF\\n" + json.dumps({
                    "working_hypothesis": "visitor feels unheard when they disagree while doing most repair work",
                    "thread_summary": "repair effort feels one-sided and disagreement leaves the visitor feeling unheard",
                    "underlying_need": "understand what happens before feeling unheard and which repair work feels one-sided",
                    "body_of_thought": "disagreement, feeling unheard, and one-sided repair work are connected while motives remain unknown",
                }),
            }],
            max_tokens=600,
            parse=json.loads,
            operation="hrn_relational",
        )
    assert shape_routed["provider"] == "nvidia", (
        "A corrected short HRN response should retain the original candidate."
    )
    assert shape_call.call_count == 2, (
        "A short HRN response receives exactly one bounded field-level correction."
    )
    assert len(shape_routed["parsed"]["response"]) >= 180

    # Fast provider failures may traverse multiple independent relational lanes,
    # but only while the existing five-second aggregate window remains open.
    fast_fallback_pool = [
        {"provider": "openrouter", "model": "openrouter/free", "index": 0},
        {"provider": "mistral", "model": "mistral-small-latest", "index": 0},
        {"provider": "nvidia", "model": "nvidia/nemotron-3-super-120b-a12b", "index": 0},
    ]
    rate_limited = provider_bank.ProviderCallError(
        "HTTP 429: Rate limit exceeded", "mistral", "mistral-small-latest",
        status_code=429, category="rate_limited",
    )
    with (
        patch.dict(os.environ, {"USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS": "1"}, clear=False),
        patch.object(provider_bank, "select", return_value=fast_fallback_pool),
        patch.object(provider_bank, "_call", side_effect=["not-json", rate_limited, valid_hrn]) as fast_call,
        patch.object(provider_bank, "_STATE", {"models": {}, "provider_cursor": 0, "model_cursors": {}, "quality": {}}),
        patch.object(provider_bank, "acquire_probe", return_value=True),
        patch.object(provider_bank, "_success"),
    ):
        fast_routed = provider_bank.route(
            use_core=None,
            messages=[{
                "role": "user",
                "content": "STRUCTURED MOVEMENT BRIEF\\n" + json.dumps({
                    "working_hypothesis": "visitor feels unheard when they disagree while doing most repair work",
                    "thread_summary": "repair effort feels one-sided and disagreement leaves the visitor feeling unheard",
                    "underlying_need": "understand what happens before feeling unheard and which repair work feels one-sided",
                    "body_of_thought": "disagreement, feeling unheard, and one-sided repair work are connected while motives remain unknown",
                }),
            }],
            max_tokens=600,
            parse=json.loads,
            operation="hrn_relational",
        )
    assert fast_routed and fast_routed["provider"] == "nvidia", (
        "A third independent provider should be tried when earlier failures are fast."
    )
    assert fast_call.call_count == 3, "Fast failures should advance through bounded independent lanes."

    # A 9.27s first failure exceeds the nine-second relational fast-failure window.
    # It must return control to the WordPress mirror boundary instead of spending
    # another provider timeout inside the same primary request.
    with (
        patch.dict(os.environ, {"USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS": "1"}, clear=False),
        patch.object(provider_bank, "select", return_value=fast_fallback_pool),
        patch.object(provider_bank, "_call", side_effect=["not-json", rate_limited, valid_hrn]) as measured_call,
        patch.object(provider_bank, "_STATE", {"models": {}, "provider_cursor": 0, "model_cursors": {}, "quality": {}}),
        patch.object(provider_bank, "acquire_probe", return_value=True),
        patch.object(provider_bank, "_success"),
        patch.object(provider_bank.time, "monotonic", side_effect=[0.0, 9.27]),
    ):
        measured_routed = provider_bank.route(
            use_core=None,
            messages=[{
                "role": "user",
                "content": "STRUCTURED MOVEMENT BRIEF\\n" + json.dumps({
                    "working_hypothesis": "visitor feels unheard when they disagree while doing most repair work",
                    "thread_summary": "repair effort feels one-sided and disagreement leaves the visitor feeling unheard",
                    "underlying_need": "understand what happens before feeling unheard and which repair work feels one-sided",
                    "body_of_thought": "disagreement, feeling unheard, and one-sided repair work are connected while motives remain unknown",
                }),
            }],
            max_tokens=600,
            parse=json.loads,
            operation="hrn_relational",
        )
    assert measured_routed is None
    assert measured_call.call_count == 1, "A slow first failure must yield to the mirror."

    # Once the nine-second fast-failure window is exceeded, the extra provider must not run.
    with (
        patch.dict(os.environ, {"USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS": "1"}, clear=False),
        patch.object(provider_bank, "select", return_value=fast_fallback_pool),
        patch.object(provider_bank, "_call", side_effect=["not-json", rate_limited]) as over_budget_call,
        patch.object(provider_bank, "_STATE", {"models": {}, "provider_cursor": 0, "model_cursors": {}, "quality": {}}),
        patch.object(provider_bank, "acquire_probe", return_value=True),
        patch.object(provider_bank, "_success"),
        patch.object(provider_bank.time, "monotonic", side_effect=[0.0, 9.01, 9.01, 9.01, 9.01]),
    ):
        over_budget_routed = provider_bank.route(
            use_core=None,
            messages=[{
                "role": "user",
                "content": "STRUCTURED MOVEMENT BRIEF\\n" + json.dumps({
                    "working_hypothesis": "visitor feels unheard when they disagree while doing most repair work",
                    "thread_summary": "repair effort feels one-sided and disagreement leaves the visitor feeling unheard",
                    "underlying_need": "understand what happens before feeling unheard and which repair work feels one-sided",
                    "body_of_thought": "disagreement, feeling unheard, and one-sided repair work are connected while motives remain unknown",
                }),
            }],
            max_tokens=600,
            parse=json.loads,
            operation="hrn_relational",
        )
    assert over_budget_routed is None
    assert over_budget_call.call_count == 1, "The extra provider must be skipped after three seconds."

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

    # NVIDIA Nemotron 3-series models that can emit reasoning separately
    # must return visitor-facing content with thinking disabled and bounded IO.
    for nvidia_model in (
        "nvidia/nemotron-3.5-lightning-30b-a3b",
        "nvidia/nemotron-3-super-120b-a12b",
    ):
        captured = {}
        def fake_nvidia_http(url, headers, payload, provider, model, timeout=6):
            captured.update({"payload": payload, "provider": provider, "model": model, "timeout": timeout})
            return {"choices": [{"message": {"content": json.dumps({"response": "The interaction becomes easier to read when intent and impact are kept distinct. Your account shows the effect of the exchange, but it does not establish what the other person intended.", "question": "What happens immediately after you explain your intent?"})}}]}
        with patch.object(provider_bank, "_http_json", side_effect=fake_nvidia_http):
            provider_bank._openai_compatible(
                "https://integrate.api.nvidia.com/v1", "test-key", "nvidia",
                nvidia_model, [{"role": "system", "content": "Return JSON."}], 128, schema=None,
            )
        assert captured["payload"]["chat_template_kwargs"] == {"enable_thinking": False}
        assert captured["timeout"] == 12

    # Normalize only a leading hedge into a grounded but still qualified
    # reflection. Keep the visitor-language validator active after normalization.
    for raw, expected in (
        ("It sounds like you explain your intent because you want them to see you as caring.",
         "From what you describe, you explain your intent because you want them to see you as caring."),
        ("It seems as though you feel the argument becomes about whether you care.",
         "From what you describe, you feel the argument becomes about whether you care."),
    ):
        repaired = provider_bank._repair_leading_hrn_hedge(raw)
        assert repaired == expected
        assert not provider_bank._hrn_surface_language_violation(repaired)
    assert provider_bank._hrn_surface_language_violation(
        "The visitor said it sounds like care is being questioned."
    ) == "it sounds like"

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

    print("v489.79 provider resilience and NVIDIA non-thinking recovery QA: PASS")

if __name__ == "__main__":
    main()
