from pathlib import Path
"""Regression tests for bounded General Guide provider arbitration."""
import pytest
import json

import provider_bank


def _item(provider, model):
    return {
        "provider": provider,
        "model": model,
        "health_state": "healthy",
        "quality_failures": 0,
        "transport_failures": 0,
        "consecutive_failures": 0,
        "last_success": 100.0,
        "capabilities": ["json_object", "long_context", "composition"],
    }


def _isolate(monkeypatch):
    candidates = [
        _item("gemini", "gemini-3.8-flash"),
        _item("workers_ai", "@cf/google/gemma-4-26b-a4b-it"),
        _item("groq", "openai/gpt-oss-20b"),
        _item("mistral", "mistral-small-latest"),
    ]
    monkeypatch.setattr(provider_bank, "select", lambda *args, **kwargs: candidates)
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    monkeypatch.setattr(provider_bank, "_blocked", lambda state, operation=None: False)
    monkeypatch.setattr(provider_bank, "acquire_probe", lambda state: True)
    monkeypatch.setattr(provider_bank, "_failure", lambda *args, **kwargs: None)
    monkeypatch.setattr(provider_bank, "_success", lambda *args, **kwargs: None)
    monkeypatch.setattr(provider_bank, "_record_quality_rejection", lambda *args, **kwargs: None)
    states = {}

    def fake_state(provider, model):
        key = provider + ":" + model
        if key not in states:
            states[key] = provider_bank.new_state(provider, model)
        return states[key]

    monkeypatch.setattr(provider_bank, "_state", fake_state)
    monkeypatch.setattr(provider_bank, "_normalize_operation_result", lambda operation, parsed, messages=None: parsed)


def test_general_guide_uses_bounded_timeout_and_one_independent_fallback(monkeypatch):
    _isolate(monkeypatch)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def fake_call(use_core, item, messages, max_tokens, schema, timeout_override=None):
        calls.append((item["provider"], timeout_override))
        if len(calls) == 1:
            clock.value += 1.0
            raise RuntimeError("simulated fast provider failure")
        return json.dumps({"response": "A grounded answer in three short paragraphs."})

    monkeypatch.setattr(provider_bank, "_call", fake_call)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": "Return one JSON object."}],
        max_tokens=1200,
        parse=provider_bank._json_object,
        operation="general_guide_composition",
    )

    assert result is not None
    assert result["provider"] == "workers_ai"
    assert calls[0][0] == "gemini"
    assert calls[1][0] == "workers_ai"
    assert all(
        provider_bank.GENERAL_GUIDE_MIN_CALL_TIMEOUT_SECONDS <= timeout <= provider_bank.GENERAL_GUIDE_MAX_CALL_TIMEOUT_SECONDS
        for _, timeout in calls
    )



def test_general_guide_uses_remaining_independent_candidates_within_window(monkeypatch):
    _isolate(monkeypatch)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def fast_failures_then_success(use_core, item, messages, max_tokens, schema, timeout_override=None):
        calls.append((item["provider"], timeout_override))
        clock.value += 0.25
        raise RuntimeError("simulated fast provider failure")

    monkeypatch.setattr(provider_bank, "_call", fast_failures_then_success)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": "Return one JSON object."}],
        max_tokens=1200,
        parse=provider_bank._json_object,
        operation="general_guide_composition",
    )

    assert result is None
    assert [provider for provider, _ in calls] == ["gemini", "workers_ai", "groq", "mistral"]
    assert all(
        provider_bank.GENERAL_GUIDE_MIN_CALL_TIMEOUT_SECONDS <= timeout <= provider_bank.GENERAL_GUIDE_MAX_CALL_TIMEOUT_SECONDS
        for _, timeout in calls
    )
    assert provider_bank.GENERAL_GUIDE_FAST_FALLBACK_MAX_CANDIDATES == 6
    assert clock.value == pytest.approx(1.0)


def test_general_guide_prioritizes_healthy_lane_over_half_open_probe(monkeypatch):
    candidates = [
        {**_item("workers_ai", "@cf/google/gemma-4-26b-a4b-it"), "health_state": "half_open", "last_success": 90.0},
        {**_item("nvidia", "nvidia/nemotron-3.5-lightning-30b-a3b"), "health_state": "healthy", "last_success": 80.0},
        {**_item("groq", "openai/gpt-oss-20b"), "health_state": "half_open", "last_success": 70.0},
    ]
    monkeypatch.setattr(provider_bank, "candidates", lambda *args, **kwargs: candidates)
    monkeypatch.setattr(provider_bank, "_csv", lambda _name: [])
    monkeypatch.setitem(provider_bank._STATE, "provider_cursor", 0)
    monkeypatch.setitem(provider_bank._STATE, "model_cursors", {})

    selected = provider_bank.select(use_core=None, operation="general_guide_composition")

    assert selected
    assert selected[0]["provider"] == "nvidia"
    assert selected[0]["health_state"] == "healthy"



def test_general_guide_interleaves_independent_provider_lanes(monkeypatch):
    candidates = [
        _item("workers_ai", "@cf/google/gemma-4-26b-a4b-it"),
        _item("workers_ai", "@cf/meta/llama-3.3-70b-instruct-fp8-fast"),
        _item("nvidia", "nvidia/nemotron-3.5-lightning-30b-a3b"),
        _item("groq", "openai/gpt-oss-20b"),
    ]
    monkeypatch.setattr(provider_bank, "candidates", lambda *args, **kwargs: candidates)
    monkeypatch.setattr(provider_bank, "_csv", lambda _name: ["workers_ai", "nvidia", "groq"])
    monkeypatch.setitem(provider_bank._STATE, "provider_cursor", 0)
    monkeypatch.setitem(provider_bank._STATE, "model_cursors", {})

    selected = provider_bank.select(use_core=None, operation="general_guide_composition")
    providers = [item["provider"] for item in selected]

    assert len(providers) == 4
    assert len(set(providers[:3])) == 3
    assert providers[3] == "workers_ai"

def test_general_guide_caps_fallbacks_after_fast_failures(monkeypatch):
    _isolate(monkeypatch)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def failures_then_success(use_core, item, messages, max_tokens, schema, timeout_override=None):
        calls.append((item["provider"], timeout_override))
        clock.value += 0.2
        raise RuntimeError("simulated fast provider failure")

    monkeypatch.setattr(provider_bank, "_call", failures_then_success)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": "Return one JSON object."}],
        max_tokens=1200,
        parse=provider_bank._json_object,
        operation="general_guide_composition",
    )

    assert result is None
    assert [provider for provider, _ in calls] == ["gemini", "workers_ai", "groq", "mistral"]
    assert all(
        provider_bank.GENERAL_GUIDE_MIN_CALL_TIMEOUT_SECONDS <= timeout <= provider_bank.GENERAL_GUIDE_MAX_CALL_TIMEOUT_SECONDS
        for _, timeout in calls
    )
    assert clock.value == pytest.approx(0.8)

def test_general_guide_stops_after_slow_failure_consumes_recovery_margin(monkeypatch):
    _isolate(monkeypatch)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def slow_failure(use_core, item, messages, max_tokens, schema, timeout_override=None):
        calls.append((item["provider"], timeout_override))
        clock.value += float(timeout_override)
        raise RuntimeError("simulated slow provider failure")

    monkeypatch.setattr(provider_bank, "_call", slow_failure)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": "Return one JSON object."}],
        max_tokens=1200,
        parse=provider_bank._json_object,
        operation="general_guide_composition",
    )

    assert result is None
    assert calls
    assert all(
        provider_bank.GENERAL_GUIDE_MIN_CALL_TIMEOUT_SECONDS <= timeout <= provider_bank.GENERAL_GUIDE_MAX_CALL_TIMEOUT_SECONDS
        for _, timeout in calls
    )
    assert provider_bank.GENERAL_GUIDE_FAST_FAILURE_WINDOW_SECONDS == 15.0
    assert provider_bank.GENERAL_GUIDE_FAST_FALLBACK_MAX_CANDIDATES == 6
    assert clock.value <= provider_bank.GENERAL_GUIDE_FAST_FAILURE_WINDOW_SECONDS

def test_request_budget_clamps_provider_timeout_and_stops_fallback(monkeypatch):
    _isolate(monkeypatch)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def consume_remaining_budget(use_core, item, messages, max_tokens, schema, timeout_override=None):
        calls.append((item["provider"], timeout_override))
        clock.value = 4.8
        raise RuntimeError("simulated failure near request deadline")

    monkeypatch.setattr(provider_bank, "_call", consume_remaining_budget)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": "Return one JSON object."}],
        max_tokens=1200,
        parse=provider_bank._json_object,
        operation="general_guide_composition",
        deadline_monotonic=5.0,
    )

    assert result is None
    assert calls == [("gemini", 5.0)]
    assert clock.value == pytest.approx(4.8)


def test_request_budget_refuses_provider_call_when_less_than_one_second_remains(monkeypatch):
    _isolate(monkeypatch)

    class Clock:
        value = 4.25

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []
    monkeypatch.setattr(
        provider_bank, "_call",
        lambda *args, **kwargs: calls.append(kwargs.get("timeout_override")),
    )
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": "Return one JSON object."}],
        max_tokens=1200,
        parse=provider_bank._json_object,
        operation="general_guide_composition",
        deadline_monotonic=5.0,
    )

    assert result is None
    assert calls == []


def test_shared_request_budget_allows_only_one_repair_with_six_seconds_reserved():
    from guide_request_budget import can_attempt_repair

    assert can_attempt_repair(24.0, already_attempted=False, now=18.0)
    assert not can_attempt_repair(24.0, already_attempted=True, now=10.0)
    assert not can_attempt_repair(24.0, already_attempted=False, now=18.01)


def _predictive_candidate(provider, model, **telemetry):
    item = _item(provider, model)
    item.update(telemetry)
    return item

def _select_predictive_lane(monkeypatch, items):
    monkeypatch.setattr(provider_bank, "candidates", lambda *args, **kwargs: items)
    monkeypatch.setattr(provider_bank, "_csv", lambda _name: [items[0]["provider"]])
    monkeypatch.setitem(provider_bank._STATE, "provider_cursor", 0)
    monkeypatch.setitem(provider_bank._STATE, "model_cursors", {})
    return provider_bank.select(use_core=None, operation="general_guide_composition")

def test_predictive_assignment_prefers_observed_deadline_fit_when_telemetry_is_ready(monkeypatch):
    slow = _predictive_candidate("gemini", "slow", latency_attempts=5, recent_timeouts=0, ewma_latency_seconds=3.5, capabilities=["composition"])
    fast = _predictive_candidate("gemini", "fast", latency_attempts=5, recent_timeouts=0, ewma_latency_seconds=0.5, capabilities=["composition"])
    assert [item["model"] for item in _select_predictive_lane(monkeypatch, [slow, fast])[:2]] == ["fast", "slow"]

def test_predictive_assignment_preserves_baseline_order_with_thin_telemetry(monkeypatch):
    first = _predictive_candidate("gemini", "first", latency_attempts=2, recent_timeouts=2, ewma_latency_seconds=9.0, capabilities=["composition"])
    second = _predictive_candidate("gemini", "second", latency_attempts=2, recent_timeouts=0, ewma_latency_seconds=0.1, capabilities=["composition"])
    assert [item["model"] for item in _select_predictive_lane(monkeypatch, [first, second])[:2]] == ["first", "second"]

def test_predictive_assignment_never_promotes_unhealthy_model_over_healthy_model(monkeypatch):
    unhealthy = _predictive_candidate("gemini", "unhealthy", health_state="half_open", latency_attempts=8, ewma_latency_seconds=0.1, capabilities=["composition"])
    healthy = _predictive_candidate("gemini", "healthy", health_state="healthy", latency_attempts=8, ewma_latency_seconds=3.5, capabilities=["composition"])
    assert _select_predictive_lane(monkeypatch, [unhealthy, healthy])[0]["model"] == "healthy"

def test_general_guide_success_outcome_includes_fresh_shadow_metrics():
    source = Path("provider_bank.py").read_text(encoding="utf-8")
    assert "outcome=success, elapsed_seconds=" in source
    assert "_predictive_shadow_metrics(state, _provider_call_timeout(operation, item))" in source

def test_general_guide_extended_provider_window_preserves_one_integrity_repair():
    from guide_request_budget import REQUEST_BUDGET_SECONDS, REPAIR_RESERVE_SECONDS

    assert provider_bank.GENERAL_GUIDE_FAST_FAILURE_WINDOW_SECONDS == 15.0
    assert (
        REQUEST_BUDGET_SECONDS - provider_bank.GENERAL_GUIDE_FAST_FAILURE_WINDOW_SECONDS
        >= REPAIR_RESERVE_SECONDS
    )



def test_quota_guarded_call_forwards_operation_to_request_correlation(monkeypatch):
    released = []
    observed = []

    class Reservation:
        def settle_output(self, result):
            return None

        def release(self):
            released.append(True)

    monkeypatch.setattr(provider_bank, "reserve_provider_call", lambda *args, **kwargs: Reservation())
    monkeypatch.setattr(provider_bank, "_call", lambda *args, **kwargs: "{}")
    monkeypatch.setattr(
        provider_bank,
        "_gold_star_provider_route_log_fields",
        lambda operation: observed.append(operation) or "",
    )

    result = provider_bank._quota_guarded_call(
        use_core=None,
        item=_item("gemini", "gemini-3.8-flash"),
        messages=[{"role": "user", "content": "Return JSON."}],
        max_tokens=100,
        schema=None,
        timeout_override=1.0,
        operation="claim_adjudication",
    )

    assert result == "{}"
    assert observed == ["claim_adjudication"]
    assert released == [True]


def test_quota_reservation_is_released_even_if_correlation_logging_raises(monkeypatch):
    released = []

    class Reservation:
        def settle_output(self, result):
            return None

        def release(self):
            released.append(True)

    monkeypatch.setattr(provider_bank, "reserve_provider_call", lambda *args, **kwargs: Reservation())
    monkeypatch.setattr(provider_bank, "_call", lambda *args, **kwargs: "{}")

    def broken_log_fields(_operation):
        raise RuntimeError("telemetry formatting failed")

    monkeypatch.setattr(provider_bank, "_gold_star_provider_route_log_fields", broken_log_fields)

    with pytest.raises(RuntimeError, match="telemetry formatting failed"):
        provider_bank._quota_guarded_call(
            use_core=None,
            item=_item("gemini", "gemini-3.8-flash"),
            messages=[{"role": "user", "content": "Return JSON."}],
            max_tokens=100,
            schema=None,
            timeout_override=1.0,
            operation="claim_adjudication",
        )

    assert released == [True]


def test_provider_route_candidate_snapshot_is_bounded_and_excludes_sensitive_fields(monkeypatch):
    candidates = [
        {
            **_item("gemini", "gemini-3.8-flash"),
            "last_success": 100.0,
            "credential_fingerprint": "DO_NOT_LOG_THIS",
            "api_key": "SECRET",
        },
        _item("workers_ai", "@cf/google/gemma-4-26b-a4b-it"),
    ]
    monkeypatch.setattr(provider_bank.time, "time", lambda: 130.0)
    snapshot = provider_bank._provider_route_candidate_snapshot(candidates, limit=1)
    assert snapshot.startswith("1:gemini/gemini-3.8-flash[health=healthy")
    assert "last_success_age_seconds=30" in snapshot
    assert "workers_ai" not in snapshot
    assert "DO_NOT_LOG_THIS" not in snapshot
    assert "SECRET" not in snapshot


def test_general_guide_half_open_probes_use_short_timeout_and_preserve_fallbacks(monkeypatch):
    _isolate(monkeypatch)
    candidates = [
        {**_item("mistral", "mistral-small-latest"), "health_state": "half_open"},
        {**_item("workers_ai", "@cf/zai-org/glm-4.7-flash"), "health_state": "half_open"},
        {**_item("openrouter", "nvidia/nemotron-3-ultra-550b-a55b:free"), "health_state": "half_open"},
        {**_item("gemini", "gemini-3.8-flash"), "health_state": "half_open"},
        {**_item("groq", "openai/gpt-oss-20b"), "health_state": "half_open"},
        {**_item("nvidia", "google/gemma-4-31b-it"), "health_state": "half_open"},
        {**_item("workers_ai", "@cf/meta/llama-3.3-70b-instruct-fp8-fast"), "health_state": "half_open"},
    ]
    monkeypatch.setattr(provider_bank, "select", lambda *args, **kwargs: candidates)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def fast_probe_failure(use_core, item, messages, max_tokens, schema, timeout_override=None):
        calls.append((item["provider"], timeout_override))
        clock.value += 0.1
        raise RuntimeError("simulated half-open probe failure")

    monkeypatch.setattr(provider_bank, "_call", fast_probe_failure)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": "Return one JSON object."}],
        max_tokens=1200,
        parse=provider_bank._json_object,
        operation="general_guide_composition",
    )

    assert result is None
    assert [provider for provider, _ in calls] == [
        "mistral", "workers_ai", "openrouter", "gemini",
        "groq", "nvidia", "workers_ai",
    ]
    assert all(
        timeout == provider_bank.GENERAL_GUIDE_HALF_OPEN_PROBE_TIMEOUT_SECONDS
        for _, timeout in calls
    )
    assert clock.value == pytest.approx(0.7)


def test_general_guide_reserves_the_next_half_open_probe_timeout(monkeypatch):
    _isolate(monkeypatch)
    candidates = [
        {**_item("mistral", "mistral-small-latest"), "health_state": "half_open"},
        {**_item("workers_ai", "@cf/zai-org/glm-4.7-flash"), "health_state": "half_open"},
        {**_item("openrouter", "nvidia/nemotron-3-ultra-550b-a55b:free"), "health_state": "half_open"},
        {**_item("gemini", "gemini-3.8-flash"), "health_state": "half_open"},
        {**_item("groq", "openai/gpt-oss-20b"), "health_state": "half_open"},
        {**_item("nvidia", "google/gemma-4-31b-it"), "health_state": "half_open"},
        {**_item("workers_ai", "@cf/meta/llama-3.3-70b-instruct-fp8-fast"), "health_state": "half_open"},
    ]
    monkeypatch.setattr(provider_bank, "select", lambda *args, **kwargs: candidates)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def timeout_failures(use_core, item, messages, max_tokens, schema, timeout_override=None):
        calls.append((item["provider"], timeout_override))
        clock.value += timeout_override
        raise RuntimeError("simulated full half-open probe timeout")

    monkeypatch.setattr(provider_bank, "_call", timeout_failures)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": "Return one JSON object."}],
        max_tokens=1200,
        parse=provider_bank._json_object,
        operation="general_guide_composition",
    )

    assert result is None
    assert len(calls) == 6
    assert all(
        timeout == provider_bank.GENERAL_GUIDE_HALF_OPEN_PROBE_TIMEOUT_SECONDS
        for _, timeout in calls
    )
    assert clock.value == pytest.approx(15.0)


def _recovery_candidate(
    provider,
    model,
    *,
    quality_failures=0,
    transport_failures=0,
    consecutive_failures=0,
    last_success=0,
    low_latency=False,
):
    item = _item(provider, model)
    item.update({
        "health_state": "half_open",
        "quality_failures": quality_failures,
        "transport_failures": transport_failures,
        "consecutive_failures": consecutive_failures,
        "last_success": last_success,
        "ewma_latency_seconds": 0.0,
        "latency_attempts": 0,
        "recent_timeouts": 0,
    })
    if low_latency:
        item["capabilities"] = list(item["capabilities"]) + ["low_latency"]
    return item


def _select_guide_recovery_candidates(monkeypatch, items):
    monkeypatch.setattr(
        provider_bank, "candidates",
        lambda *args, **kwargs: [dict(item) for item in items],
    )
    monkeypatch.setattr(provider_bank, "_csv", lambda _name: [])
    monkeypatch.setattr(
        provider_bank, "_provider_call_timeout", lambda *args, **kwargs: 4.0
    )
    monkeypatch.setattr(
        provider_bank, "_STATE",
        {"models": {}, "quality": {}, "provider_cursor": 0, "model_cursors": {}},
    )
    return provider_bank.select(
        object(), operation="general_guide_composition", schema=None
    )


def test_general_guide_half_open_recovery_prefers_proven_transport_lanes(monkeypatch):
    selected = _select_guide_recovery_candidates(
        monkeypatch,
        [
            _recovery_candidate(
                "mistral", "mistral-small-latest",
                quality_failures=0, transport_failures=528,
                consecutive_failures=9, low_latency=True,
            ),
            _recovery_candidate(
                "workers_ai", "@cf/zai-org/glm-4.7-flash",
                quality_failures=0, transport_failures=621,
                consecutive_failures=11, low_latency=True,
            ),
            _recovery_candidate(
                "workers_ai", "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
                quality_failures=18, transport_failures=153,
                consecutive_failures=16, last_success=200,
            ),
            _recovery_candidate(
                "openrouter", "google/gemma-4-31b-it:free",
                quality_failures=0, transport_failures=168,
                consecutive_failures=9,
            ),
            _recovery_candidate(
                "openrouter", "nvidia/nemotron-3-ultra-550b-a55b:free",
                quality_failures=0, transport_failures=209,
                consecutive_failures=9, last_success=250,
            ),
            _recovery_candidate(
                "groq", "openai/gpt-oss-20b",
                quality_failures=3, transport_failures=7,
                consecutive_failures=6, last_success=300,
                low_latency=True,
            ),
        ],
    )

    assert [
        (item["provider"], item["model"]) for item in selected[:3]
    ] == [
        ("groq", "openai/gpt-oss-20b"),
        ("workers_ai", "@cf/meta/llama-3.3-70b-instruct-fp8-fast"),
        ("openrouter", "nvidia/nemotron-3-ultra-550b-a55b:free"),
    ]


def test_general_guide_quality_history_breaks_equal_transport_ties(monkeypatch):
    selected = _select_guide_recovery_candidates(
        monkeypatch,
        [
            _recovery_candidate(
                "workers_ai", "@cf/google/gemma-4-26b-a4b-it",
                quality_failures=4, transport_failures=10,
                consecutive_failures=2, last_success=100,
            ),
            _recovery_candidate(
                "groq", "openai/gpt-oss-20b",
                quality_failures=1, transport_failures=10,
                consecutive_failures=2, last_success=100,
            ),
        ],
    )

    assert selected[0]["provider"] == "groq"


def test_provider_tpm_preflight_skips_only_impossible_input_sizes(monkeypatch):
    from provider_quota_control import provider_input_exceeds_tpm_budget

    monkeypatch.setenv("USE_QUOTA_GROQ_TPM", "8000")
    too_large = [{"role": "user", "content": "x" * 32000}]
    fits = [{"role": "user", "content": "x" * 28000}]

    blocked = provider_input_exceeds_tpm_budget("groq", too_large)
    assert blocked == {"budget_limit": 8000, "input_estimate": 8008}
    assert provider_input_exceeds_tpm_budget("groq", fits) is None
    assert provider_input_exceeds_tpm_budget("workers_ai", too_large) is None


def test_general_guide_tpm_preflight_skips_all_models_of_impossible_provider(monkeypatch):
    _isolate(monkeypatch)
    candidates = [
        _item("groq", "openai/gpt-oss-20b"),
        _item("workers_ai", "@cf/google/gemma-4-26b-a4b-it"),
        _item("groq", "openai/gpt-oss-120b"),
        _item("mistral", "mistral-small-latest"),
    ]
    monkeypatch.setattr(provider_bank, "select", lambda *args, **kwargs: [dict(x) for x in candidates])
    monkeypatch.setenv("USE_QUOTA_GROQ_TPM", "8000")
    calls = []

    def succeed(use_core, item, messages, max_tokens, schema, timeout_override=None):
        calls.append(item["provider"])
        return json.dumps({"response": "A grounded answer in three short paragraphs."})

    monkeypatch.setattr(provider_bank, "_call", succeed)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "user", "content": "x" * 32000}],
        max_tokens=100,
        parse=provider_bank._json_object,
        operation="general_guide_composition",
    )

    assert result is not None
    assert calls == ["workers_ai"]
    assert result["provider"] == "workers_ai"




def test_general_guide_skips_final_partial_window_below_supported_minimum(monkeypatch, capsys):
    _isolate(monkeypatch)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def two_timeouts_then_exhaustion(use_core, item, messages, max_tokens, schema, timeout_override=None):
        calls.append((item["provider"], timeout_override))
        clock.value += float(timeout_override) + 0.02
        raise RuntimeError("simulated provider timeout")

    monkeypatch.setattr(provider_bank, "_call", two_timeouts_then_exhaustion)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": "Return one JSON object."}],
        max_tokens=1200,
        parse=provider_bank._json_object,
        operation="general_guide_composition",
    )

    assert result is None
    assert [provider for provider, _ in calls] == ["gemini", "workers_ai"]
    assert [timeout for _, timeout in calls] == pytest.approx([5.0, 5.0])
    # Two failed attempts consume 10.04 seconds of the 15-second window.
    # The remaining 4.96 seconds cannot support a normal five-second attempt.
    assert clock.value == pytest.approx(10.04)
    assert provider_bank.GENERAL_GUIDE_FAST_FAILURE_WINDOW_SECONDS == pytest.approx(15.0)
    output = capsys.readouterr().out
    assert "action=skip_candidate_below_minimum_timeout" in output
    assert "candidate_timeout_seconds=4.96" in output
    assert "minimum_timeout_seconds=5.00" in output
    assert "reason=insufficient_remaining_time" in output
