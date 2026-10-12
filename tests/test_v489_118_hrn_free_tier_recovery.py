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




def test_hrn_relational_uses_quality_history_when_transport_health_is_equal(monkeypatch):
    candidates = [
        _item("nvidia", "nvidia/nemotron-3-super-120b-a12b", quality=3, consecutive=0, transport=0, last_success=999),
        _item("groq", "openai/gpt-oss-120b", quality=0, consecutive=0, transport=0, last_success=100),
    ]
    monkeypatch.setattr(provider_bank, "candidates", lambda use_core, operation="generic", schema=None: candidates)
    monkeypatch.setattr(provider_bank, "_csv", lambda name: ["nvidia", "groq"])
    provider_bank._STATE["provider_cursor"] = 0
    provider_bank._STATE["model_cursors"] = {}
    provider_bank._STATE["models"].clear()
    provider_bank._STATE["quality"].clear()

    selected = provider_bank.select(None, operation="hrn_relational")

    assert [item["provider"] for item in selected[:2]] == ["groq", "nvidia"]


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
    monkeypatch.setattr(provider_bank, "_call", lambda use_core, item, *a, **kw: calls.append(item["provider"]) or '{"response":"You described feeling unheard during disagreements. The conversation seems to end before your point has been fully acknowledged, leaving both the disagreement and your experience unresolved. There is a difference between disagreeing about a topic and feeling unheard while the conversation is happening.","question":"What happened in the most recent conversation?","rest":false,"use_resource":false,"resource_intro":""}')
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
    attempts = []
    def fake_call(use_core, item, *args, **kwargs):
        attempts.append(item["provider"])
        if item["provider"] == "nvidia":
            return '{"response":"You should consider telling the other person how you feel and asking them to listen more carefully. That may help create a different outcome.","question":"What happened next?"}'
        return '{"response":"You said you feel unheard when you and your friend disagree. You want to understand what happens between you in those moments without assuming what your friend intends. The difference between disagreeing about a topic and feeling unheard during the conversation is worth looking at separately.","question":"Can you share a recent example of a disagreement where you felt unheard?"}'
    monkeypatch.setattr(provider_bank, "_call", fake_call)
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


def test_hrn_relational_tries_multiple_independent_fast_fallbacks(monkeypatch):
    candidates = [
        _item("groq", "openai/gpt-oss-120b"),
        _item("gemini", "gemini-3.8-flash"),
        _item("mistral", "mistral-small-latest"),
        _item("workers_ai", "@cf/meta/llama-3.3-70b-instruct-fp8-fast"),
    ]
    monkeypatch.setattr(provider_bank, "select", lambda *args, **kwargs: candidates)
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    monkeypatch.setattr(provider_bank, "_state", lambda provider, model: provider_bank.new_state(provider, model))
    monkeypatch.setattr(provider_bank, "_record_quality_rejection", lambda *args, **kwargs: None)
    monkeypatch.setattr(provider_bank, "_success", lambda *args, **kwargs: None)
    monkeypatch.setattr(provider_bank, "_failure", lambda *args, **kwargs: None)

    attempts = []

    def fake_call(use_core, item, *args, **kwargs):
        provider = item["provider"]
        attempts.append(provider)
        if provider == "groq":
            return '{"response":"The disagreement concerns which part of the project each person treats as fixed. One points to the agreed date, while the other points to the changed scope.","question":"What changes when you look at the situation through that distinction?"}'
        if provider == "gemini":
            raise provider_bank.ProviderCallError("temporary 503", provider, item["model"], category="http_error")
        if provider == "mistral":
            return '{"response":"The disagreement concerns which part of the project each person treats as fixed. One points to the agreed date, while the other points to the changed scope.","question":"What changes when you look at the situation through that distinction?"}'
        return '{"response":"One colleague is treating the agreed date as a commitment, while the other is pointing to the changed scope as a change in the work itself. The disagreement therefore concerns whether the original date still describes the project now on the table.","question":"What happens in their conversation when the agreed date is raised alongside the changed scope?","rest":false,"use_resource":false,"resource_intro":""}'

    monkeypatch.setattr(provider_bank, "_call", fake_call)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "system", "content": "Return one JSON object."}],
        max_tokens=300,
        parse=provider_bank._json_object,
        operation="hrn_relational",
    )

    assert result and result["provider"] == "workers_ai"
    assert attempts == ["groq", "gemini", "mistral", "workers_ai"]



def test_explicit_provider_timeout_can_be_shorter_than_default_floor(monkeypatch):
    observed = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"ok": true}'

    def fake_urlopen(request, timeout=None):
        observed["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(provider_bank.urllib.request, "urlopen", fake_urlopen)
    result = provider_bank._http_json(
        "https://provider.example.test/endpoint",
        {},
        {"ping": True},
        "test_provider",
        "test_model",
        timeout=1.0,
    )

    assert result == {"ok": True}
    assert observed["timeout"] == 1.0


def test_hrn_call_timeout_constant_is_inside_fast_failure_budget():
    assert provider_bank.HRN_PROVIDER_CALL_TIMEOUT_SECONDS == 1.0
    assert provider_bank.HRN_PROVIDER_CALL_TIMEOUT_SECONDS < provider_bank.HRN_RELATIONAL_FAST_FAILURE_WINDOW_SECONDS
