"""Regression tests for evidence-led Guide provider recovery ordering."""

import provider_bank


def _candidate(
    provider,
    model,
    *,
    health_state="half_open",
    quality_failures=0,
    transport_failures=0,
    consecutive_failures=0,
    last_success=0,
    low_latency=False,
):
    capabilities = ["json_object", "long_context", "composition"]
    if low_latency:
        capabilities.append("low_latency")
    return {
        "provider": provider,
        "model": model,
        "index": 0,
        "quality_failures": quality_failures,
        "health_state": health_state,
        "transport_failures": transport_failures,
        "consecutive_failures": consecutive_failures,
        "last_success": last_success,
        "ewma_latency_seconds": 0.0,
        "latency_attempts": 0,
        "recent_timeouts": 0,
        "capabilities": capabilities,
    }


def _select_guide(monkeypatch, candidates):
    monkeypatch.setattr(
        provider_bank,
        "candidates",
        lambda *args, **kwargs: [dict(item) for item in candidates],
    )
    monkeypatch.setattr(provider_bank, "_csv", lambda _name: [])
    monkeypatch.setattr(
        provider_bank, "_provider_call_timeout", lambda *args, **kwargs: 4.0
    )
    monkeypatch.setattr(
        provider_bank,
        "_STATE",
        {"models": {}, "quality": {}, "provider_cursor": 0, "model_cursors": {}},
    )
    return provider_bank.select(
        object(), operation="general_guide_composition", schema=None
    )


def test_guide_half_open_recovery_prefers_proven_transport_lanes(monkeypatch):
    selected = _select_guide(
        monkeypatch,
        [
            _candidate(
                "mistral", "mistral-small-latest",
                quality_failures=0, transport_failures=528,
                consecutive_failures=9, low_latency=True,
            ),
            _candidate(
                "workers_ai", "@cf/zai-org/glm-4.7-flash",
                quality_failures=0, transport_failures=621,
                consecutive_failures=11, low_latency=True,
            ),
            _candidate(
                "workers_ai", "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
                quality_failures=18, transport_failures=153,
                consecutive_failures=16, last_success=200,
            ),
            _candidate(
                "openrouter", "google/gemma-4-31b-it:free",
                quality_failures=0, transport_failures=168,
                consecutive_failures=9,
            ),
            _candidate(
                "openrouter", "nvidia/nemotron-3-ultra-550b-a55b:free",
                quality_failures=0, transport_failures=209,
                consecutive_failures=9, last_success=250,
            ),
            _candidate(
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


def test_healthy_guide_lane_still_precedes_half_open_recovery(monkeypatch):
    selected = _select_guide(
        monkeypatch,
        [
            _candidate(
                "groq", "openai/gpt-oss-20b",
                health_state="half_open", quality_failures=0,
                transport_failures=1, last_success=900,
            ),
            _candidate(
                "mistral", "mistral-small-latest",
                health_state="healthy", quality_failures=8,
                transport_failures=500, last_success=500,
            ),
        ],
    )

    assert selected[0]["provider"] == "mistral"
    assert selected[0]["health_state"] == "healthy"


def test_quality_history_remains_a_tiebreaker_after_transport_evidence(monkeypatch):
    selected = _select_guide(
        monkeypatch,
        [
            _candidate(
                "workers_ai", "@cf/google/gemma-4-26b-a4b-it",
                quality_failures=4, transport_failures=10,
                consecutive_failures=2, last_success=100,
            ),
            _candidate(
                "groq", "openai/gpt-oss-20b",
                quality_failures=1, transport_failures=10,
                consecutive_failures=2, last_success=100,
            ),
        ],
    )

    assert selected[0]["provider"] == "groq"
