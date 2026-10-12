"""Regression tests for bounded HRN provider selection and recovery.

These tests require no live credentials and never call an external provider.
"""
import os
import time
import provider_bank


def _item(provider, model, *, health="healthy", quality=0, transport=0, consecutive=0, last_success=100.0, capabilities=None):
    return {
        "provider": provider, "model": model, "health_state": health,
        "quality_failures": quality, "transport_failures": transport,
        "consecutive_failures": consecutive, "last_success": last_success,
        "capabilities": list(capabilities or ["json_object", "long_context", "composition", "relational_analysis"]),
    }


def test_hrn_relational_selection_prefers_quality_success_when_health_is_equal(monkeypatch):
    candidates = [
        _item("nvidia", "nvidia/nemotron-3-super-120b-a12b", quality=3, consecutive=0, last_success=999),
        _item("groq", "openai/gpt-oss-120b", quality=0, consecutive=0, last_success=100),
        _item("openrouter", "openrouter/free", quality=0, consecutive=1, last_success=500),
    ]
    monkeypatch.setattr(provider_bank, "candidates", lambda use_core, operation="generic", schema=None: candidates)
    monkeypatch.setattr(provider_bank, "_csv", lambda name: ["nvidia", "groq", "openrouter"])
    provider_bank._STATE["provider_cursor"] = 0
    provider_bank._STATE["model_cursors"] = {}
    provider_bank._STATE["models"].clear()
    provider_bank._STATE["quality"].clear()
    selected = provider_bank.select(None, operation="hrn_relational")
    assert [x["provider"] for x in selected[:3]] == ["groq", "openrouter", "nvidia"]


def test_hrn_relational_rechecks_blocked_state_before_provider_call(monkeypatch):
    # A candidate can enter cooldown after candidates() snapshots its state.
    monkeypatch.setattr(provider_bank, "candidates", lambda use_core, operation="generic", schema=None: [
        _item("groq", "openai/gpt-oss-120b"),
        _item("nvidia", "nvidia/nemotron-3-super-120b-a12b"),
    ])
    original_state_fn = provider_bank._state
    original_models = provider_bank._STATE["models"]
    original_quality = provider_bank._STATE["quality"]
    saved_models = original_models.copy()
    saved_quality = original_quality.copy()
    original_models.clear()
    original_quality.clear()
    calls = []

    def fake_state(provider, model):
        key = provider + ":" + model
        state = provider_bank.new_state(provider, model)
        if provider == "groq":
            state.update({"state": "open", "cooldown_until": time.time() + 120, "quarantine_until": 0, "category": "rate_limited"})
        else:
            state.update({"state": "healthy", "cooldown_until": 0, "quarantine_until": 0, "category": ""})
        original_models[key] = state
        return state

    monkeypatch.setattr(provider_bank, "_state", fake_state)
    monkeypatch.setattr(provider_bank, "_call", lambda use_core, item, *a, **kw: calls.append(item["provider"]) or '{"response":"You said you feel unheard when you and your friend disagree. You want to understand what happens between you in those moments without assuming what your friend intends. The difference between disagreeing about a topic and feeling unheard during the conversation is worth looking at separately.","question":"Can you share a recent example of a disagreement where you felt unheard?","rest":false,"use_resource":false,"resource_intro":""}')
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    try:
        result = provider_bank.route(use_core=None, messages=[{"role": "system", "content": "Return JSON only."}], max_tokens=300, parse=provider_bank._json_object, operation="hrn_relational")
    finally:
        monkeypatch.setattr(provider_bank, "_state", original_state_fn)
        original_models.clear()
        original_models.update(saved_models)
        original_quality.clear()
        original_quality.update(saved_quality)
    assert result and result["provider"] == "nvidia"
    assert calls == ["nvidia"]


def test_hrn_relational_contract_rejection_is_quality_failure_not_provider_failure(monkeypatch):
    # A syntactically valid response that fails the human-surface contract
    # must not trigger a same-model correction/retry.
    monkeypatch.setattr(provider_bank, "candidates", lambda use_core, operation="generic", schema=None: [
        _item("nvidia", "nvidia/nemotron-3-super-120b-a12b"),
        _item("groq", "openai/gpt-oss-120b"),
    ])
    attempts = []
    monkeypatch.setattr(provider_bank, "_call", lambda use_core, item, *a, **kw: (
        attempts.append(item["provider"]) or (
            '{"response":"When a disagreement leaves you feeling unheard, the friction is rarely just about the topic being debated. It often reveals a gap between reaching an agreement and simply acknowledging what the other person actually experienced. Noticing whether the struggle is about winning a point or making room for two distinct viewpoints allows you to see where the conversation stops being a shared dialogue.","question":"What feels different when you hold both sides together?","rest":false,"use_resource":false,"resource_intro":""}'
            if item["provider"] == "nvidia" else
            '{"response":"You said you feel unheard when you and your friend disagree. You want to understand what happens between you in those moments without assuming what your friend intends. The difference between disagreeing about a topic and feeling unheard during the conversation is worth looking at separately.","question":"Can you share a recent example of a disagreement where you felt unheard?","rest":false,"use_resource":false,"resource_intro":""}'
        )
    ))
    original_sync = provider_bank._sync_shared_state
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    original_persist = provider_bank._persist_shared_state
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    try:
        result = provider_bank.route(use_core=None, messages=[{"role":"system","content":"Return a JSON object."}], max_tokens=300, parse=provider_bank._json_object, operation="hrn_relational")
    finally:
        monkeypatch.setattr(provider_bank, "_sync_shared_state", original_sync)
        monkeypatch.setattr(provider_bank, "_persist_shared_state", original_persist)
    assert result and result["provider"] == "groq"
    assert attempts == ["nvidia", "groq"]


def test_hrn_free_attempt_cap_is_bounded():
    old = os.environ.get("USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS")
    try:
        os.environ.pop("USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS", None)
        assert provider_bank._hrn_attempt_cap() == 1
        os.environ["USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS"] = "2"
        assert provider_bank._hrn_attempt_cap() == 2
        os.environ["USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS"] = "50"
        assert provider_bank._hrn_attempt_cap() == 2
        os.environ["USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS"] = "bad"
        assert provider_bank._hrn_attempt_cap() == 1
    finally:
        if old is None:
            os.environ.pop("USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS", None)
        else:
            os.environ["USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS"] = old
