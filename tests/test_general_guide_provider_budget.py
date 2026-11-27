from pathlib import Path
"""Regression tests for bounded General Guide provider arbitration."""
import pytest
import json

import provider_bank
import gold_star_lessons
import general_guide_composition as guide_composition
import provider_quota_control
from provider_quota_control import estimate_input_tokens


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
    assert provider_bank.GENERAL_GUIDE_FAST_FAILURE_WINDOW_SECONDS == 18.0
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

    assert provider_bank.GENERAL_GUIDE_FAST_FAILURE_WINDOW_SECONDS == 18.0
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


def test_nvidia_nemotron_super_vl_half_open_probe_gets_full_bounded_composition_timeout():
    item = {
        **_item("nvidia", "nvidia/nemotron-3.5-super-vl-120b-a12b"),
        "health_state": "half_open",
    }
    timeout = provider_bank._provider_call_timeout("general_guide_composition", item)
    assert timeout == pytest.approx(5.5)
    assert timeout <= provider_bank.GENERAL_GUIDE_FAST_FAILURE_WINDOW_SECONDS


def test_healthy_nvidia_lightning_gets_six_point_five_second_margin_after_live_timeout(monkeypatch):
    model = "nvidia/nemotron-3.5-lightning-30b-a3b"
    # 2.74s EWMA produces the former 5.1s timeout; live acceptance later
    # observed 6.032s on a complete held-out community-rule transfer.
    monkeypatch.setitem(provider_bank._PROVIDER_LATENCY_EWMA, ("nvidia", model), 2.74)
    healthy = {**_item("nvidia", model), "health_state": "healthy"}
    timeout = provider_bank._provider_call_timeout("general_guide_composition", healthy)
    assert timeout == pytest.approx(6.5)
    assert timeout > 6.032
    assert timeout <= provider_bank.GENERAL_GUIDE_FAST_FAILURE_WINDOW_SECONDS

    # Do not lengthen half-open probes; preserve their existing bounded policy.
    half_open = {**healthy, "health_state": "half_open"}
    assert provider_bank._provider_call_timeout(
        "general_guide_composition", half_open
    ) == provider_bank.GENERAL_GUIDE_HALF_OPEN_PROBE_TIMEOUT_SECONDS


def test_general_guide_half_open_candidates_receive_composition_timeout_and_preserve_fallbacks(monkeypatch):
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


def test_general_guide_half_open_candidate_can_finish_after_old_probe_timeout(monkeypatch):
    _isolate(monkeypatch)
    candidate = {
        **_item("nvidia", "nvidia/nemotron-3.5-lightning-30b-a3b"),
        "health_state": "half_open",
    }
    monkeypatch.setattr(provider_bank, "select", lambda *args, **kwargs: [candidate])

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def valid_composition_after_three_seconds(use_core, item, messages, max_tokens, schema, timeout_override=None):
        calls.append(timeout_override)
        assert timeout_override == provider_bank.GENERAL_GUIDE_MIN_CALL_TIMEOUT_SECONDS
        clock.value += 3.25
        return json.dumps({"response": "A complete, grounded answer in three purposeful paragraphs."})

    monkeypatch.setattr(provider_bank, "_call", valid_composition_after_three_seconds)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": "Return one JSON object."}],
        max_tokens=1200,
        parse=provider_bank._json_object,
        operation="general_guide_composition",
    )

    assert result is not None
    assert result["provider"] == "nvidia"
    assert calls == [provider_bank.GENERAL_GUIDE_MIN_CALL_TIMEOUT_SECONDS]
    assert clock.value == pytest.approx(3.25)


def test_general_guide_reserves_the_next_half_open_composition_timeout(monkeypatch):
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
    # A slow full composition receives the supported 5s minimum. The 18s
    # arbitration window therefore admits three timed-out recovery candidates,
    # rather than seven calls that cannot finish a substantive answer.
    assert len(calls) == 3
    assert all(
        timeout == provider_bank.GENERAL_GUIDE_MIN_CALL_TIMEOUT_SECONDS
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


def test_general_guide_half_open_recovery_prefers_current_streak_and_recent_success(monkeypatch):
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
        ("openrouter", "nvidia/nemotron-3-ultra-550b-a55b:free"),
        ("workers_ai", "@cf/meta/llama-3.3-70b-instruct-fp8-fast"),
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
    # The former 15-second window stranded the third provider after two
    # ordinary five-second timeouts (10.04s elapsed, 4.96s left). The
    # 18-second window admits one more independent candidate while retaining
    # the six-second integrity-repair reserve in the shared 24-second budget.
    assert [provider for provider, _ in calls] == ["gemini", "workers_ai", "groq"]
    assert [timeout for _, timeout in calls] == pytest.approx([5.0, 5.0, 5.0])
    assert clock.value == pytest.approx(15.06)
    assert provider_bank.GENERAL_GUIDE_FAST_FAILURE_WINDOW_SECONDS == pytest.approx(18.0)
    output = capsys.readouterr().out
    assert "action=skip_candidate_below_minimum_timeout" in output
    assert "candidate_timeout_seconds=2.94" in output
    assert "minimum_timeout_seconds=5.00" in output
    assert "reason=insufficient_remaining_time" in output



def test_general_guide_rechecks_minimum_timeout_at_transport_boundary(monkeypatch, capsys):
    _isolate(monkeypatch)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    bounded_calls = {"count": 0}

    def shrink_at_transport_boundary(timeout, deadline_monotonic, now=None):
        bounded_calls["count"] += 1
        if bounded_calls["count"] >= 4:
            return min(float(timeout), 4.99)
        return float(timeout)

    monkeypatch.setattr(
        provider_bank,
        "_bounded_request_provider_timeout",
        shrink_at_transport_boundary,
    )
    calls = []

    def first_candidate_fails(use_core, item, messages, max_tokens, schema, timeout_override=None):
        calls.append((item["provider"], timeout_override))
        clock.value += 0.1
        raise RuntimeError("simulated provider failure")

    monkeypatch.setattr(provider_bank, "_call", first_candidate_fails)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": "Return one JSON object."}],
        max_tokens=1200,
        parse=provider_bank._json_object,
        operation="general_guide_composition",
        deadline_monotonic=100.0,
    )

    assert result is None
    # The first attempt is allowed; the fallback is skipped after its final
    # deadline recheck shrinks the transport timeout to 4.99 seconds.
    assert [provider for provider, _ in calls] == ["gemini"]
    assert calls[0][1] == pytest.approx(5.0)
    output = capsys.readouterr().out
    assert "reason=deadline_recheck_insufficient_remaining_time" in output
    assert "candidate_timeout_seconds=4.99" in output
    assert "minimum_timeout_seconds=5.00" in output


def test_community_rule_prompt_loads_only_relevant_task_modules_and_keeps_default_doorway():
    question = "How should a community decide whether limits on personal liberty are justified by shared obligations and risks?"
    prompt = guide_composition._build_general_guide_system_prompt(
        question, gold_star_guidance=True
    )

    assert "QUESTION-FIRST, TASK-DEPENDENT COMPOSITION GOVERNANCE" in prompt
    assert "For consequential action under uncertainty" in prompt
    assert "GOLD STAR INTEGRATION RULE" in prompt
    assert "A doorway is a separate but default part of the Guide's role" in prompt
    assert "include one concise, verified Living Archive destination" in prompt
    assert "AUTONOMY, ADAPTIVITY, RESILIENCE, AND IMPROVEMENT" not in prompt
    assert "GOLD STAR REMEDY SELECTION" not in prompt
    assert "QUOTED-PASSAGE CONTEXT RESTORATION" not in prompt
    assert "COMMUNITY PROJECT TRADE-OFF QUESTIONS" not in prompt


def test_guide_system_prompt_retains_meta_evaluation_modules_only_for_meta_questions():
    question = "How can we validate Gold Star adaptive learning transfer and decide whether a recurring failure needs engineering repair?"
    prompt = guide_composition._build_general_guide_system_prompt(question)

    assert "AUTONOMY, ADAPTIVITY, RESILIENCE, AND IMPROVEMENT" in prompt
    assert "Separate the claims and identify evidence appropriate to each" in prompt
    assert "Explain how to make the evidence credible" in prompt
    assert "GOLD STAR SCOPE GOVERNANCE" in prompt
    assert "GOLD STAR REMEDY SELECTION" in prompt


def test_guide_system_prompt_keeps_navigation_links_out_of_visitor_prose():
    prompt = guide_composition._build_general_guide_system_prompt(
        "How should a community decide whether limits on personal liberty are justified?"
    )

    assert "Never include raw URLs or Markdown links in visitor prose" in prompt
    assert "the Guide attaches verified doorway links separately" in prompt


def test_community_rule_gold_star_prompt_fits_configured_groq_tpm_budget():
    question = "How should a community decide whether limits on personal liberty are justified by shared obligations and risks?"
    quality = gold_star_lessons.active_quality_contribution(question)
    assert quality and len(quality.get("candidates") or []) == 4
    adjudication_instruction = guide_composition._build_gold_star_quality_instruction(quality)
    assert "An unclassified role is not disqualifying" in adjudication_instruction
    assert "Decide before drafting" in adjudication_instruction
    assert "Return exact 12–120-character response offsets" in adjudication_instruction
    assert "rejected IDs use 0,0. Reject if no range" in adjudication_instruction
    messages = guide_composition._build_general_guide_provider_messages(
        question,
        "U" * 7000,
        has_gold_star_guidance=True,
        incomplete_knowledge_plan=guide_composition.build_incomplete_knowledge_plan(question),
        gold_star_quality_instruction=adjudication_instruction,
        public_live_source_instruction=guide_composition._public_live_source_security_instruction(
            {"live_source_evidence_provenance": [{"source": "verified-live-archive-test-fixture"}]}
        ),
        objective_integrity_instruction=guide_composition._objective_integrity_instruction(question),
    )

    assert guide_composition.GENERAL_GUIDE_PROVIDER_USER_CONTENT_MAX_CHARS == 6400
    assert len(messages[1]["content"]) == 6400
    assert estimate_input_tokens(messages) + 750 <= 8000


def test_relational_synthesis_gold_star_prompt_preserves_privacy_boundary():
    quality = {
        "candidates": [{
            "benchmark_id": "general-guide-relational-synthesis-concept-pairs-2026-11-24",
            "role": "CORE",
            "reasoning_family": "relational_synthesis_concept_pairs",
            "transferable_discipline": "Distinguish each concept's role and explain the mechanism.",
            "abstention_boundary": (
                "Do not force relational synthesis onto simple definitions. Preserve domain-specific evidence limits, "
                "privacy, and legitimate confidentiality. Never infer unsupported causation or guarantees."
            ),
            "activation_condition": "active_quality_contributor",
            "score": 1.0,
        }]
    }
    instruction = guide_composition._build_gold_star_quality_instruction(quality)
    assert "privacy and legitimate confidentiality" in instruction
    assert "meaningful boundary or tension" in instruction


def test_gold_star_quality_standard_remains_active_when_no_candidate_is_available():
    prompt = guide_composition._build_general_guide_system_message(
        "How should a community make a fair decision?",
        has_gold_star_guidance=False,
    )

    assert "GOLD STAR ADAPTIVE INTELLIGENCE STANDARD v2.0" in prompt
    assert "PROSE" in prompt
    assert "ADAPTIVE LEARNING INTEGRITY" in prompt
    assert "GOLD STAR MULTI-CANDIDATE ADJUDICATION" not in prompt
    assert "LAYERED ANSWERABILITY" in prompt


def test_successful_provider_route_issues_execution_proof_and_invocation_id(monkeypatch):
    _isolate(monkeypatch)

    monkeypatch.setattr(
        provider_bank,
        "_call",
        lambda *args, **kwargs: json.dumps(
            {"response": "A complete answer from the controlled provider."}
        ),
    )

    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": "Return one JSON object."}],
        max_tokens=1200,
        parse=provider_bank._json_object,
        operation="general_guide_composition",
    )

    assert result is not None
    assert result["_provider_execution_verified"] is True
    assert isinstance(result["_provider_invocation_id"], str)
    assert len(result["_provider_invocation_id"]) == 32
    assert result["provider"] == "gemini"


def test_failed_provider_route_never_issues_execution_proof_or_invocation_id(monkeypatch):
    _isolate(monkeypatch)

    def fail_provider(*args, **kwargs):
        raise RuntimeError("controlled provider transport failure")

    monkeypatch.setattr(provider_bank, "_call", fail_provider)

    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": "Return one JSON object."}],
        max_tokens=1200,
        parse=provider_bank._json_object,
        operation="general_guide_composition",
    )

    assert result is None



def test_failed_provider_call_refunds_unused_output_quota_for_fallback(monkeypatch):
    provider_quota_control._reset_for_tests()
    monkeypatch.setenv("USE_QUOTA_TESTPROVIDER_TPM", "220")
    item = _item("testprovider", "test-model")
    messages = [{"role": "user", "content": "Q" * 100}]
    attempts = []

    def fail_once_then_succeed(use_core, selected, request_messages, max_tokens, schema, timeout_override=None):
        attempts.append(selected["model"])
        if len(attempts) == 1:
            raise RuntimeError("simulated upstream failure")
        return provider_bank.ProviderOutput("A valid fallback response.", completion_tokens=6)

    monkeypatch.setattr(provider_bank, "_call", fail_once_then_succeed)

    with pytest.raises(RuntimeError, match="simulated upstream failure"):
        provider_bank._quota_guarded_call(
            use_core=None,
            item=item,
            messages=messages,
            max_tokens=50,
            schema=None,
            timeout_override=5.0,
            operation="general_guide_composition",
        )

    # The failed attempt retains its estimated input charge but must not retain
    # the unused 50-token completion reservation.
    fallback = provider_bank._quota_guarded_call(
        use_core=None,
        item=item,
        messages=messages,
        max_tokens=50,
        schema=None,
        timeout_override=5.0,
        operation="general_guide_composition",
    )

    assert str(fallback) == "A valid fallback response."
    assert attempts == ["test-model", "test-model"]


def test_competing_values_balance_contract_fits_groq_budget_without_gold_star_candidate():
    question = "How should an organization balance stability, participation, and responsiveness?"
    system = guide_composition._build_general_guide_system_message(question)
    assert "COMPETING-VALUES AND GOVERNANCE-BALANCE REASONING" in system
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "U" * 7000},
    ]
    assert estimate_input_tokens(messages) + 750 <= 8000


def test_answer_first_boundary_rejects_question_and_source_prefaces():
    question = "What is the difference between growth, adaptation, maturity, and integration?"

    assert not guide_composition._has_direct_answer_opening(
        question,
        "Your question asks: what is the difference between growth, adaptation, maturity, and integration? "
        "The Archive material available here offers this starting point.",
    )
    assert not guide_composition._has_direct_answer_opening(
        question,
        "The question is about the difference between growth, adaptation, maturity, and integration. "
        "A related Archive resource may help explore it.",
    )
    assert not guide_composition._has_direct_answer_opening(
        question,
        "The Archive material available here offers this starting point: From Self-Development to the Care of What Endures.",
    )


def test_answer_first_boundary_accepts_a_substantive_comparative_opening():
    question = "What is the difference between growth, adaptation, maturity, and integration?"
    response = (
        "Growth expands a system's capacities, adaptation changes how it responds to conditions, "
        "maturity develops discernment and stability, and integration brings its parts into coherent relationship."
    )

    assert guide_composition._has_direct_answer_opening(question, response)


def test_provider_parser_rejects_question_narration_before_archive_orientation():
    question = "What is the difference between growth, adaptation, maturity, and integration?"
    parse = guide_composition._parse_factory([], query=question, emit_telemetry=False)
    response = (
        "Your question asks: what is the difference between growth, adaptation, maturity, and integration? "
        "The Archive material available here offers this starting point."
    )

    with pytest.raises(ValueError, match="hard answer-first visitor boundary"):
        parse(json.dumps({"response": response}))


def test_initial_composition_reserves_six_seconds_for_integrity_repair():
    from guide_request_budget import composition_provider_deadline

    assert composition_provider_deadline(24.0, now=0.0) == 18.0
    assert composition_provider_deadline(24.0, now=20.0) == 20.0
    assert composition_provider_deadline(None, now=0.0) is None


def test_integrity_recovery_composition_can_use_the_reserved_deadline():
    from guide_request_budget import composition_provider_deadline

    assert composition_provider_deadline(
        24.0, integrity_recovery=True, now=20.0
    ) == 24.0


def test_initial_and_internal_composition_retries_share_the_reserved_deadline():
    source = Path("general_guide_composition.py").read_text(encoding="utf-8")

    assert "from guide_request_budget import composition_provider_deadline" in source
    assert "provider_deadline_monotonic = composition_provider_deadline(" in source
    # Initial composition, internal retry, and each independent task-fit
    # repair must consume the same request-reserved provider deadline.
    assert source.count("deadline_monotonic=provider_deadline_monotonic") == 4


def test_general_guide_prefers_recent_success_and_lower_failure_streak_over_stale_transport_totals(monkeypatch):
    candidates = [
        {
            **_item("groq", "openai/gpt-oss-120b"),
            "health_state": "half_open",
            "last_success": 100.0,
            "transport_failures": 29,
            "consecutive_failures": 6,
            "quality_failures": 47,
        },
        {
            **_item("nvidia", "nvidia/nemotron-3.5-super-vl-120b-a12b"),
            "health_state": "half_open",
            "last_success": 200.0,
            "transport_failures": 116,
            "consecutive_failures": 1,
            "quality_failures": 1,
        },
        {
            **_item("mistral", "mistral-small-latest"),
            "health_state": "half_open",
            "last_success": 0.0,
            "transport_failures": 609,
            "consecutive_failures": 18,
            "quality_failures": 0,
        },
    ]
    monkeypatch.setattr(provider_bank, "candidates", lambda *args, **kwargs: candidates)
    monkeypatch.setattr(provider_bank, "_csv", lambda _name: ["groq", "nvidia", "mistral"])
    monkeypatch.setitem(provider_bank._STATE, "provider_cursor", 0)
    monkeypatch.setitem(provider_bank._STATE, "model_cursors", {})

    selected = provider_bank.select(use_core=None, operation="general_guide_composition")

    assert [item["provider"] for item in selected[:3]] == ["nvidia", "groq", "mistral"]


def test_definition_significance_matcher_recognizes_present_day_qualifier():
    query = "What is stewardship and why does it matter now more than ever?"

    assert guide_composition._definition_significance_subject(query) == "stewardship"
    assert guide_composition._has_direct_definition_for_subject(
        query,
        "Stewardship means making responsible decisions about shared resources.",
    )
    assert not guide_composition._has_direct_definition_for_subject(
        query,
        "Responsible choices matter because they affect other people.",
    )


def test_half_open_nvidia_super_vl_timeout_preserves_a_proven_sibling_fallback_slot(monkeypatch):
    _isolate(monkeypatch)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    candidates = [
        {
            **_item("nvidia", "nvidia/nemotron-3.5-super-vl-120b-a12b"),
            "health_state": "half_open",
            "capabilities": ["composition", "reasoning"],
        },
        {
            **_item("groq", "openai/gpt-oss-120b"),
            "capabilities": ["composition", "reasoning", "low_latency"],
        },
        {
            **_item("workers_ai", "@cf/google/gemma-4-26b-a4b-it"),
            "capabilities": ["composition", "reasoning"],
        },
        {
            **_item("nvidia", "nvidia/nemotron-3.5-lightning-30b-a3b"),
            "capabilities": ["composition", "reasoning", "low_latency"],
        },
    ]
    monkeypatch.setattr(provider_bank, "select", lambda *args, **kwargs: candidates)
    calls = []

    def fail_slow_lanes_then_reach_lightning(use_core, item, messages, max_tokens, schema, timeout_override=None):
        calls.append((item["provider"], item["model"], timeout_override))
        if item["model"] == "nvidia/nemotron-3.5-super-vl-120b-a12b":
            clock.value += float(timeout_override)
            raise RuntimeError("simulated half-open Super VL timeout")
        if item["provider"] == "groq":
            clock.value += 0.08
            raise RuntimeError("simulated fast Groq failure")
        if item["provider"] == "workers_ai":
            clock.value += 5.0
            raise RuntimeError("simulated Workers AI timeout")
        clock.value += 2.7
        return json.dumps({"response": "A complete answer from the lower-latency NVIDIA sibling."})

    monkeypatch.setattr(provider_bank, "_call", fail_slow_lanes_then_reach_lightning)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": "Return one JSON object."}],
        max_tokens=1200,
        parse=provider_bank._json_object,
        operation="general_guide_composition",
    )

    assert result is not None
    assert result["provider"] == "nvidia"
    assert result["model"] == "nvidia/nemotron-3.5-lightning-30b-a3b"
    assert calls[0][2] == pytest.approx(5.5)
    assert calls[-1][1] == "nvidia/nemotron-3.5-lightning-30b-a3b"


def test_transparency_trust_prompt_module_is_omitted_from_community_liberty_question():
    question = (
        "How should a community decide whether limits on personal liberty are justified "
        "by shared obligations and risks?"
    )
    prompt = guide_composition._build_general_guide_system_prompt(question)

    assert "COMPETING-VALUES AND GOVERNANCE-BALANCE REASONING" in prompt
    assert "TRANSPARENCY AND TRUST RECIPROCITY" not in prompt


def test_embedded_navigation_url_is_a_repairable_response_shape_failure():
    reason = "general composition embedded a navigation URL in visitor prose"

    assert provider_bank._contract_rejection_class(reason) == "response_shape"


def test_guide_lane_prefers_recent_success_over_stale_model_preference(monkeypatch):
    """A recently proven Lightning candidate outranks an unproven preferred sibling."""
    candidates = [
        {
            "provider": "nvidia",
            "model": "nvidia/nemotron-3.5-super-vl-120b-a12b",
            "health_state": "healthy",
            "quality_failures": 0,
            "transport_failures": 0,
            "consecutive_failures": 0,
            "last_success": 0,
            "ewma_latency_seconds": 0,
            "latency_attempts": 0,
            "recent_timeouts": 0,
            "capabilities": ["composition", "relational_analysis"],
        },
        {
            "provider": "nvidia",
            "model": "nvidia/nemotron-3.5-lightning-30b-a3b",
            "health_state": "healthy",
            "quality_failures": 0,
            "transport_failures": 8,
            "consecutive_failures": 0,
            "last_success": 2000,
            "ewma_latency_seconds": 5.0,
            "latency_attempts": 1,
            "recent_timeouts": 0,
            "capabilities": ["composition", "relational_analysis", "low_latency"],
        },
    ]
    monkeypatch.setattr(provider_bank, "candidates", lambda *args, **kwargs: candidates)
    monkeypatch.setattr(provider_bank, "_csv", lambda _name: [])
    monkeypatch.setattr(provider_bank, "_provider_call_timeout", lambda *args, **kwargs: 5.0)
    monkeypatch.setattr(
        provider_bank,
        "_STATE",
        {"models": {}, "quality": {}, "provider_cursor": 0, "model_cursors": {}},
    )

    selected = provider_bank.select(object(), operation="general_guide_composition")

    assert selected[0]["model"] == "nvidia/nemotron-3.5-lightning-30b-a3b"


def test_openai_compatible_adapter_extracts_typed_text_blocks(monkeypatch):
    monkeypatch.setattr(
        provider_bank,
        "_http_json",
        lambda *args, **kwargs: {
            "choices": [{
                "message": {
                    "content": [
                        {"type": "reasoning", "text": "internal only"},
                        {"type": "text", "text": '{"response": '},
                        {"type": "output_text", "text": '"A grounded answer."}'},
                    ],
                    "reasoning_content": "must not be surfaced",
                },
                "finish_reason": "stop",
            }],
            "usage": {"completion_tokens": 42},
        },
    )

    output = provider_bank._openai_compatible(
        "https://api.nvidia.com/v1",
        "test-key",
        "nvidia",
        "nvidia/nemotron-3.5-lightning-30b-a3b",
        [{"role": "user", "content": "test"}],
        200,
        schema={"mode": "text"},
        timeout=5,
    )

    assert str(output) == '{"response": "A grounded answer."}'
    assert output.completion_tokens == 42


def test_openai_compatible_adapter_never_substitutes_reasoning_for_content(monkeypatch):
    monkeypatch.setattr(
        provider_bank,
        "_http_json",
        lambda *args, **kwargs: {
            "choices": [{
                "message": {
                    "content": None,
                    "reasoning_content": "private reasoning without an answer",
                },
                "finish_reason": "stop",
            }],
        },
    )

    with pytest.raises(provider_bank.ProviderCallError) as error:
        provider_bank._openai_compatible(
            "https://api.nvidia.com/v1",
            "test-key",
            "nvidia",
            "nvidia/nemotron-3.5-lightning-30b-a3b",
            [{"role": "user", "content": "test"}],
            200,
            schema={"mode": "text"},
            timeout=5,
        )

    assert error.value.category == "invalid_provider_response"



@pytest.mark.parametrize(
    ("reason", "expected"),
    [
        ("community liberty-limit answer is incomplete: affected_party_participation", "community_rule_incomplete"),
        ("transparency-trust answer must explain both directions of influence", "transparency_trust_reciprocity"),
        ("transparency-trust answer must explicitly preserve privacy", "transparency_trust_disclosure_boundary"),
        ("substantive multi-idea answer must preserve semantic paragraph boundaries", "semantic_paragraph_boundaries"),
        ("provider response embedded navigation URLs in visitor prose", "embedded_navigation_url"),
        ("general composition returned invalid JSON", "invalid_json"),
        ("unclassified safe validator rejection", "other_contract"),
    ],
)
def test_contract_rejection_reason_telemetry_is_bounded_and_content_free(reason, expected):
    assert provider_bank._contract_rejection_reason_code(reason) == expected



def test_openai_compatible_adapter_preserves_paragraph_separators_between_text_blocks(monkeypatch):
    monkeypatch.setattr(
        provider_bank,
        "_http_json",
        lambda *args, **kwargs: {
            "choices": [{
                "message": {
                    "content": [
                        {"type": "reasoning", "text": "must remain hidden"},
                        {"type": "text", "text": "First paragraph has a distinct function. It develops one idea.\n\n"},
                        {"type": "output_text", "text": "Second paragraph advances the next idea. It adds a consequence."},
                    ],
                },
                "finish_reason": "stop",
            }],
        },
    )

    output = provider_bank._openai_compatible(
        "https://api.nvidia.com/v1",
        "test-key",
        "nvidia",
        "nvidia/nemotron-3.5-lightning-30b-a3b",
        [{"role": "user", "content": "test"}],
        200,
        schema={"mode": "text"},
        timeout=5,
    )

    assert str(output) == (
        "First paragraph has a distinct function. It develops one idea.\n\n"
        "Second paragraph advances the next idea. It adds a consequence."
    )
    assert "must remain hidden" not in str(output)
