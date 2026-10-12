"""Regression tests for transport-health-first HRN provider arbitration."""
import provider_bank


def _candidate(provider, model, *, health, quality, consecutive, failures, last_success):
    return {
        "provider": provider,
        "model": model,
        "index": 0,
        "quality_failures": quality,
        "health_state": health,
        "transport_failures": failures,
        "consecutive_failures": consecutive,
        "last_success": last_success,
        "capabilities": [],
    }


def test_hrn_relational_prefers_healthy_transport_over_half_open_with_cleaner_quality_history(monkeypatch):
    candidates = [
        _candidate("gemini", "gemini-3.8-flash", health="half_open", quality=0, consecutive=4, failures=45, last_success=100),
        _candidate("mistral", "mistral-small-latest", health="half_open", quality=0, consecutive=29, failures=123, last_success=0),
        _candidate("nvidia", "nvidia/nemotron-3-super-120b-a12b", health="healthy", quality=2, consecutive=0, failures=6, last_success=200),
    ]
    monkeypatch.setattr(provider_bank, "candidates", lambda *args, **kwargs: [dict(item) for item in candidates])
    monkeypatch.setattr(provider_bank, "_csv", lambda name: ["gemini", "mistral", "nvidia"])
    monkeypatch.setattr(provider_bank, "_STATE", {"models": {}, "quality": {}, "provider_cursor": 0, "model_cursors": {}})

    selected = provider_bank.select(object(), operation="hrn_relational")

    assert selected
    assert selected[0]["provider"] == "nvidia"
    assert selected[0]["health_state"] == "healthy"


def test_hrn_relational_keeps_quality_history_as_tiebreaker_within_same_health_tier(monkeypatch):
    candidates = [
        _candidate("groq", "openai/gpt-oss-120b", health="healthy", quality=2, consecutive=0, failures=3, last_success=200),
        _candidate("nvidia", "nvidia/nemotron-3.5-lightning-30b-a3b", health="healthy", quality=0, consecutive=0, failures=1, last_success=150),
    ]
    monkeypatch.setattr(provider_bank, "candidates", lambda *args, **kwargs: [dict(item) for item in candidates])
    monkeypatch.setattr(provider_bank, "_csv", lambda name: ["groq", "nvidia"])
    monkeypatch.setattr(provider_bank, "_STATE", {"models": {}, "quality": {}, "provider_cursor": 0, "model_cursors": {}})

    selected = provider_bank.select(object(), operation="hrn_relational")

    assert selected[0]["provider"] == "nvidia"
    assert selected[0]["quality_failures"] == 0
