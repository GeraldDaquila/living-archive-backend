"""Provider-bank route batches shared health writes into one route-boundary snapshot."""
import provider_bank


def _candidate(provider, model):
    return {
        "provider": provider,
        "model": model,
        "health_state": "healthy",
        "quality_failures": 0,
        "transport_failures": 0,
        "consecutive_failures": 0,
        "last_success": 100.0,
        "capabilities": ["json_object", "relational_analysis"],
    }


def test_multiple_candidate_failures_persist_one_shared_health_snapshot(monkeypatch):
    candidates = [_candidate("groq", "model-a"), _candidate("nvidia", "model-b")]
    monkeypatch.setattr(provider_bank, "select", lambda *args, **kwargs: candidates)
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_blocked", lambda state, operation=None: False)
    monkeypatch.setattr(provider_bank, "acquire_probe", lambda state: True)
    monkeypatch.setattr(provider_bank, "_STATE", {
        "models": {}, "quality": {}, "provider_cursor": 0, "model_cursors": {}
    })
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: 0.0)
    writes = []
    monkeypatch.setattr(provider_bank, "save_remote_states", lambda states: writes.append(states) or True)

    def fail_fast(use_core, item, messages, max_tokens, schema=None, timeout_override=None):
        raise provider_bank.ProviderCallError(
            "simulated independent lane 429",
            item["provider"], item["model"], 429, category="rate_limited"
        )

    monkeypatch.setattr(provider_bank, "_quota_guarded_call", fail_fast)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "user", "content": "synthetic calibration input"}],
        max_tokens=100,
        parse=provider_bank._json_object,
        operation="hrn_perception",
    )

    assert result is None
    assert len(writes) == 1
    assert set(writes[0]) >= {"groq:model-a", "nvidia:model-b"}
    assert provider_bank._PERSIST_CONTEXT.defer is False
    assert provider_bank._PERSIST_CONTEXT.dirty is False
