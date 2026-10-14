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
    monkeypatch.setattr(provider_bank, "_call", lambda use_core, item, *a, **kw: calls.append(item["provider"]) or '{"response":"You described feeling unheard during disagreements. The conversation seems to end before your point has been fully acknowledged, leaving both the disagreement and your experience unresolved. There is a difference between disagreeing about a topic and feeling unheard while the conversation is happening.","question":"What happens in the conversation when the deadline is raised alongside the changed scope?","rest":false,"use_resource":false,"resource_intro":""}')
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    try:
        result = provider_bank.route(use_core=None, messages=[{"role": "system", "content": 'STRUCTURED MOVEMENT BRIEF\n{"working_hypothesis":"deadline disagreement","thread_summary":"two colleagues disagree about the agreed date","underlying_need":"shared clarity about the date and added work","emerging_delta":"the project scope changed after the original agreement","body_of_thought":"deadline and changed scope remain in tension"}\nReturn JSON only.'}], max_tokens=300, parse=provider_bank._json_object, operation="hrn_relational")
    finally:
        monkeypatch.setattr(provider_bank, "_state", original_state_fn)
        original_models.clear()
        original_models.update(saved_models)
        original_quality.clear()
        original_quality.update(saved_quality)
    assert result and result["provider"] == "nvidia"
    assert calls == ["nvidia"]


def test_hrn_relational_contract_rejection_is_quality_failure_not_provider_failure(monkeypatch):
    # A semantic action-solution rejection must advance directly to an independent provider.
    monkeypatch.setattr(provider_bank, "candidates", lambda use_core, operation="generic", schema=None: [
        _item("nvidia", "nvidia/nemotron-3-super-120b-a12b"),
        _item("groq", "openai/gpt-oss-120b"),
    ])
    attempts = []
    attempts = []
    def fake_call(use_core, item, *args, **kwargs):
        attempts.append(item["provider"])
        if item["provider"] == "nvidia":
            return '{"response":"The disagreement is opening space to negotiate a common timeline and deliverable set, which may change how both people approach the deadline.","question":"What happened when the agreed date was raised alongside the changed scope?"}'
        return '{"response":"You said you feel unheard when you and your friend disagree. You want to understand what happens between you in those moments without assuming what your friend intends. The difference between disagreeing about a topic and feeling unheard during the conversation is worth looking at separately.","question":"What happened in the conversation when the agreed date was raised alongside the changed scope?"}'
    monkeypatch.setattr(provider_bank, "_call", fake_call)
    original_sync = provider_bank._sync_shared_state
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    original_persist = provider_bank._persist_shared_state
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    try:
        result = provider_bank.route(use_core=None, messages=[{"role":"system","content":'STRUCTURED MOVEMENT BRIEF\n{"working_hypothesis":"deadline disagreement","thread_summary":"two colleagues disagree about the agreed date","underlying_need":"shared clarity about the date and added work","emerging_delta":"the project scope changed after the original agreement","body_of_thought":"deadline and changed scope remain in tension"}\nReturn a JSON object.'}], max_tokens=300, parse=provider_bank._json_object, operation="hrn_relational")
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
        messages=[{"role": "system", "content": 'STRUCTURED MOVEMENT BRIEF\n{"working_hypothesis":"deadline disagreement","thread_summary":"two colleagues disagree about the agreed date","underlying_need":"shared clarity about the date and added work","emerging_delta":"the project scope changed after the original agreement","body_of_thought":"deadline and changed scope remain in tension"}\nReturn one JSON object.'}],
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
    assert provider_bank.HRN_PROVIDER_CALL_TIMEOUT_SECONDS == 2.5
    assert provider_bank.HRN_PROVIDER_CALL_TIMEOUT_SECONDS < provider_bank.HRN_RELATIONAL_FAST_FAILURE_WINDOW_SECONDS



def test_hrn_prescriptive_question_gets_one_targeted_recovery(monkeypatch):
    candidate = _item("nvidia", "nvidia/nemotron-3-super-120b-a12b", capabilities=["json_object", "json_schema_best_effort", "long_context", "composition", "relational_analysis"])
    monkeypatch.setattr(provider_bank, "candidates", lambda use_core, operation="generic", schema=None: [candidate])
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    original_models = provider_bank._STATE["models"]
    original_quality = provider_bank._STATE["quality"]
    saved_models = original_models.copy()
    saved_quality = original_quality.copy()
    original_models.clear()
    original_quality.clear()
    attempts = []

    response = (
        "The original estimate covered the work that had been described at the time. "
        "The additional work changed the scope after the date had already been discussed. "
        "Those are different baselines, which helps explain why the same deadline now carries a different expectation."
    )
    valid = (
        '{"response":' + __import__("json").dumps(response)
        + ',"question":"What happened in the conversation when the agreed date was raised alongside the added work?",'
        + '"rest":false,"use_resource":false,"resource_intro":""}'
    )
    rejected = (
        '{"response":' + __import__("json").dumps(response)
        + ',"question":"What should you do next?",'
        + '"rest":false,"use_resource":false,"resource_intro":""}'
    )

    recovery_schemas = []

    def fake_call(use_core, item, *args, **kwargs):
        attempts.append(item["provider"])
        if len(attempts) > 1 and len(args) >= 3:
            recovery_schemas.append(args[2])
        return rejected if len(attempts) == 1 else valid

    monkeypatch.setattr(provider_bank, "_call", fake_call)
    messages = [{
        "role": "system",
        "content": (
            'STRUCTURED MOVEMENT BRIEF\n'
            '{"working_hypothesis":"deadline disagreement",'
            '"thread_summary":"two colleagues disagree about the agreed date",'
            '"underlying_need":"clarity about the date and added work",'
            '"emerging_delta":"the project scope changed after the original agreement",'
            '"body_of_thought":"deadline and changed scope remain in tension"}\n'
            "Return one JSON object."
        ),
    }]
    try:
        result = provider_bank.route(
            use_core=None,
            messages=messages,
            max_tokens=300,
            parse=provider_bank._json_object,
            operation="hrn_relational",
        )
    finally:
        original_models.clear()
        original_models.update(saved_models)
        original_quality.clear()
        original_quality.update(saved_quality)

    assert result is not None
    assert result["parsed"]["response"] == response, "Question repair must preserve the original response."
    assert result["parsed"]["question"] == "What happened in the conversation when the agreed date was raised alongside the added work?"
    assert recovery_schemas, "Targeted question recovery did not use the dedicated schema."
    assert recovery_schemas[0]["schema"]["required"] == ["question"]
    assert set(recovery_schemas[0]["schema"]["properties"]) == {"question"}
    assert attempts == ["nvidia", "nvidia"]



def test_hrn_missing_question_gets_question_only_recovery(monkeypatch):
    import json

    candidate = _item(
        "nvidia",
        "nvidia/nemotron-3-super-120b-a12b",
        capabilities=["json_object", "json_schema_best_effort", "long_context", "composition", "relational_analysis"],
    )
    monkeypatch.setattr(provider_bank, "candidates", lambda use_core, operation="generic", schema=None: [candidate])
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    original_models = provider_bank._STATE["models"]
    original_quality = provider_bank._STATE["quality"]
    saved_models = original_models.copy()
    saved_quality = original_quality.copy()
    original_models.clear()
    original_quality.clear()
    attempts = []
    recovery_schemas = []

    response = (
        "The original estimate covered the work that had been described at the time. "
        "The additional work changed the scope after the date had already been discussed. "
        "Those are different baselines, which helps explain why the same deadline now carries a different expectation."
    )
    first_pass = json.dumps({
        "response": response,
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    })
    repaired_question = "What happened when the agreed date was raised alongside the changed scope?"

    def fake_call(use_core, item, *args, **kwargs):
        attempts.append(item["provider"])
        if len(attempts) > 1 and len(args) >= 3:
            recovery_schemas.append(args[2])
        return first_pass if len(attempts) == 1 else json.dumps({"question": repaired_question})

    monkeypatch.setattr(provider_bank, "_call", fake_call)
    messages = [{
        "role": "system",
        "content": (
            'STRUCTURED MOVEMENT BRIEF\\n'
            '{"observer_delta":"the project scope changed after the original agreement; '
            'the agreed date remains in dispute"}\\n'
            "Return one JSON object."
        ),
    }]
    try:
        result = provider_bank.route(
            use_core=None,
            messages=messages,
            max_tokens=300,
            parse=provider_bank._json_object,
            operation="hrn_relational",
        )
    finally:
        original_models.clear()
        original_models.update(saved_models)
        original_quality.clear()
        original_quality.update(saved_quality)

    assert result is not None
    assert result["parsed"]["response"] == response
    assert result["parsed"]["question"] == repaired_question
    assert recovery_schemas and recovery_schemas[0]["schema"]["required"] == ["question"]
    assert attempts == ["nvidia", "nvidia"]

def test_hrn_targeted_question_recovery_still_fails_closed(monkeypatch):
    candidate = _item("nvidia", "nvidia/nemotron-3-super-120b-a12b")
    monkeypatch.setattr(provider_bank, "candidates", lambda use_core, operation="generic", schema=None: [candidate])
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    original_models = provider_bank._STATE["models"]
    original_quality = provider_bank._STATE["quality"]
    saved_models = original_models.copy()
    saved_quality = original_quality.copy()
    original_models.clear()
    original_quality.clear()
    attempts = []

    response = (
        "The original estimate covered the work that had been described at the time. "
        "The additional work changed the scope after the date had already been discussed. "
        "Those are different baselines, which helps explain why the same deadline now carries a different expectation."
    )
    rejected = (
        '{"response":' + __import__("json").dumps(response)
        + ',"question":"What should you do next?",'
        + '"rest":false,"use_resource":false,"resource_intro":""}'
    )

    def fake_call(use_core, item, *args, **kwargs):
        attempts.append(item["provider"])
        return rejected

    monkeypatch.setattr(provider_bank, "_call", fake_call)
    messages = [{
        "role": "system",
        "content": (
            'STRUCTURED MOVEMENT BRIEF\n'
            '{"working_hypothesis":"deadline disagreement",'
            '"thread_summary":"two colleagues disagree about the agreed date",'
            '"underlying_need":"clarity about the date and added work",'
            '"emerging_delta":"the project scope changed after the original agreement",'
            '"body_of_thought":"deadline and changed scope remain in tension"}\n'
            "Return one JSON object."
        ),
    }]
    try:
        result = provider_bank.route(
            use_core=None,
            messages=messages,
            max_tokens=300,
            parse=provider_bank._json_object,
            operation="hrn_relational",
        )
    finally:
        original_models.clear()
        original_models.update(saved_models)
        original_quality.clear()
        original_quality.update(saved_quality)

    assert result is None
    assert attempts == ["nvidia", "nvidia"]



def test_hrn_short_response_gets_one_targeted_response_recovery(monkeypatch):
    import json
    candidate = _item("nvidia", "nvidia/nemotron-3-super-120b-a12b")
    monkeypatch.setattr(provider_bank, "candidates", lambda use_core, operation="generic", schema=None: [candidate])
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    original_models = provider_bank._STATE["models"]
    original_quality = provider_bank._STATE["quality"]
    saved_models = original_models.copy()
    saved_quality = original_quality.copy()
    original_models.clear()
    original_quality.clear()
    attempts = []

    short = {
        "response": "The added work changed the original scope.",
        "question": "What happened when the agreed date was discussed alongside the added work?",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }
    repaired = {
        "response": (
            "The original estimate reflected the work that had been described at the time. "
            "The added work changed that scope after the date had already been discussed. "
            "The deadline is now being judged against a larger set of expectations than the original estimate contained."
        ),
        "question": "What happened when the agreed date was discussed alongside the added work?",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }

    def fake_call(use_core, item, *args, **kwargs):
        attempts.append(item["provider"])
        return json.dumps(short if len(attempts) == 1 else repaired)

    monkeypatch.setattr(provider_bank, "_call", fake_call)
    messages = [{
        "role": "system",
        "content": (
            'STRUCTURED MOVEMENT BRIEF\n'
            '{"working_hypothesis":"deadline disagreement",'
            '"thread_summary":"two colleagues disagree about the agreed date",'
            '"underlying_need":"clarity about the date and added work",'
            '"emerging_delta":"the project scope changed after the original agreement",'
            '"body_of_thought":"deadline and changed scope remain in tension"}\n'
            "Return one JSON object."
        ),
    }]
    try:
        result = provider_bank.route(
            use_core=None,
            messages=messages,
            max_tokens=300,
            parse=provider_bank._json_object,
            operation="hrn_relational",
        )
    finally:
        original_models.clear()
        original_models.update(saved_models)
        original_quality.clear()
        original_quality.update(saved_quality)

    assert result is not None
    assert len(result["parsed"]["response"]) >= 180
    assert attempts == ["nvidia", "nvidia"]


def test_hrn_short_response_recovery_still_fails_closed(monkeypatch):
    import json
    candidate = _item("nvidia", "nvidia/nemotron-3-super-120b-a12b")
    monkeypatch.setattr(provider_bank, "candidates", lambda use_core, operation="generic", schema=None: [candidate])
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    original_models = provider_bank._STATE["models"]
    original_quality = provider_bank._STATE["quality"]
    saved_models = original_models.copy()
    saved_quality = original_quality.copy()
    original_models.clear()
    original_quality.clear()
    attempts = []

    short = {
        "response": "The added work changed the original scope.",
        "question": "What happened when the agreed date was discussed alongside the added work?",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }

    def fake_call(use_core, item, *args, **kwargs):
        attempts.append(item["provider"])
        return json.dumps(short)

    monkeypatch.setattr(provider_bank, "_call", fake_call)
    messages = [{
        "role": "system",
        "content": (
            'STRUCTURED MOVEMENT BRIEF\n'
            '{"working_hypothesis":"deadline disagreement",'
            '"thread_summary":"two colleagues disagree about the agreed date",'
            '"underlying_need":"clarity about the date and added work",'
            '"emerging_delta":"the project scope changed after the original agreement",'
            '"body_of_thought":"deadline and changed scope remain in tension"}\n'
            "Return one JSON object."
        ),
    }]
    try:
        result = provider_bank.route(
            use_core=None,
            messages=messages,
            max_tokens=300,
            parse=provider_bank._json_object,
            operation="hrn_relational",
        )
    finally:
        original_models.clear()
        original_models.update(saved_models)
        original_quality.clear()
        original_quality.update(saved_quality)

    assert result is None
    assert attempts == ["nvidia", "nvidia"]



def test_hrn_repeated_prescriptive_question_uses_grounded_lexical_fallback(monkeypatch):
    import json
    candidate = _item("nvidia", "nvidia/nemotron-3-super-120b-a12b")
    monkeypatch.setattr(provider_bank, "candidates", lambda use_core, operation="generic", schema=None: [candidate])
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    original_models = provider_bank._STATE["models"]
    original_quality = provider_bank._STATE["quality"]
    saved_models = original_models.copy()
    saved_quality = original_quality.copy()
    original_models.clear()
    original_quality.clear()
    attempts = []

    response = (
        "The original estimate covered the work that had been described at the time. "
        "The added work changed that scope after the date had already been discussed. "
        "The deadline is now being judged against a larger set of expectations than the original estimate contained."
    )
    prescriptive = {
        "response": response,
        "question": "What should you tell your colleague about the changed scope?",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }

    def fake_call(use_core, item, *args, **kwargs):
        attempts.append(item["provider"])
        return json.dumps(prescriptive)

    monkeypatch.setattr(provider_bank, "_call", fake_call)
    messages = [{
        "role": "system",
        "content": (
            'STRUCTURED MOVEMENT BRIEF\n'
            '{"working_hypothesis":"deadline disagreement",'
            '"thread_summary":"two colleagues disagree about the agreed date",'
            '"underlying_need":"clarity about the date and added work",'
            '"emerging_delta":"the project scope changed after the original agreement",'
            '"body_of_thought":"deadline and changed scope remain in tension"}\n'
            "Return one JSON object."
        ),
    }]
    try:
        result = provider_bank.route(
            use_core=None,
            messages=messages,
            max_tokens=300,
            parse=provider_bank._json_object,
            operation="hrn_relational",
        )
    finally:
        original_models.clear()
        original_models.update(saved_models)
        original_quality.clear()
        original_quality.update(saved_quality)

    assert result is not None
    assert result["parsed"]["question"] == "What stands out to you about the changed scope?"
    assert provider_bank._hrn_question_grounding_violation(
        result["parsed"]["question"], messages
    ) == ""
    assert attempts == ["nvidia", "nvidia"]



def test_hrn_relational_groq_completion_budget_preserves_response_and_question(monkeypatch):
    import json
    candidate = _item("groq", "openai/gpt-oss-20b")
    monkeypatch.setattr(provider_bank, "candidates", lambda use_core, operation="generic", schema=None: [candidate])
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    original_models = provider_bank._STATE["models"]
    original_quality = provider_bank._STATE["quality"]
    saved_models = original_models.copy()
    saved_quality = original_quality.copy()
    original_models.clear()
    original_quality.clear()
    budgets = []
    valid = {
        "response": (
            "The original estimate reflected the work that had been described at the time. "
            "The added work changed that scope after the date had already been discussed. "
            "The deadline is now being judged against a larger set of expectations than the original estimate contained."
        ),
        "question": "What happened when the agreed date was discussed alongside the added work?",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }

    def fake_call(use_core, item, *args, **kwargs):
        budgets.append(args[1])
        return json.dumps(valid)

    monkeypatch.setattr(provider_bank, "_call", fake_call)
    messages = [{
        "role": "system",
        "content": (
            'STRUCTURED MOVEMENT BRIEF\n'
            '{"working_hypothesis":"deadline disagreement",'
            '"thread_summary":"two colleagues disagree about the agreed date",'
            '"underlying_need":"clarity about the date and added work",'
            '"emerging_delta":"the project scope changed after the original agreement",'
            '"body_of_thought":"deadline and changed scope remain in tension"}\n'
            "Return one JSON object."
        ),
    }]
    try:
        result = provider_bank.route(
            use_core=None,
            messages=messages,
            max_tokens=3000,
            parse=provider_bank._json_object,
            operation="hrn_relational",
        )
    finally:
        original_models.clear()
        original_models.update(saved_models)
        original_quality.clear()
        original_quality.update(saved_quality)

    assert result is not None
    assert budgets == [700]
    assert provider_bank.HRN_RELATIONAL_MAX_COMPLETION_TOKENS == 700
    assert provider_bank.OPERATION_TOKEN_FLOORS["hrn_relational"] == 600
    assert provider_bank.OPERATION_MODEL_LIMITS[
        ("hrn_relational", "groq", "openai/gpt-oss-20b")
    ] == 700
    assert result["parsed"]["question"].strip() != ""
    assert result["parsed"]["response"].strip() != ""



def test_hrn_action_guidance_gets_one_bounded_response_recovery(monkeypatch):
    import json
    candidate = _item("groq", "openai/gpt-oss-20b")
    monkeypatch.setattr(provider_bank, "candidates", lambda use_core, operation="generic", schema=None: [candidate])
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    original_models = provider_bank._STATE["models"]
    original_quality = provider_bank._STATE["quality"]
    saved_models = original_models.copy()
    saved_quality = original_quality.copy()
    original_models.clear()
    original_quality.clear()
    attempts = []

    action_guidance = {
        "response": (
            "The added work was not part of the original estimate, and the deadline was discussed before that work was added. "
            "Seeing the change as a scope expansion lets you focus on reallocating resources or renegotiating the timeline rather than blaming time constraints alone. "
            "The disagreement now includes both the date and what work the date was meant to cover."
        ),
        "question": "What happened when the agreed date was discussed alongside the added work?",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }
    neutral = {
        "response": (
            "The original estimate covered the work described at the time, and the date was discussed against that scope. "
            "The added work arrived later, but the deadline is now being judged as though the original estimate included it. "
            "That leaves a difference between what was first agreed and what is now expected."
        ),
        "question": "What happened when the agreed date was discussed alongside the added work?",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }

    def fake_call(use_core, item, *args, **kwargs):
        attempts.append(item["provider"])
        return json.dumps(action_guidance if len(attempts) == 1 else neutral)

    monkeypatch.setattr(provider_bank, "_call", fake_call)
    messages = [{
        "role": "system",
        "content": (
            'STRUCTURED MOVEMENT BRIEF\n'
            '{"working_hypothesis":"deadline disagreement",'
            '"thread_summary":"two colleagues disagree about the agreed date",'
            '"underlying_need":"clarity about the date and added work",'
            '"emerging_delta":"the project scope changed after the original agreement",'
            '"body_of_thought":"deadline and changed scope remain in tension"}\n'
            "Return one JSON object."
        ),
    }]
    try:
        result = provider_bank.route(
            use_core=None,
            messages=messages,
            max_tokens=3000,
            parse=provider_bank._json_object,
            operation="hrn_relational",
        )
    finally:
        original_models.clear()
        original_models.update(saved_models)
        original_quality.clear()
        original_quality.update(saved_quality)

    assert result is not None
    assert "reallocating resources" not in result["parsed"]["response"].casefold()
    assert "renegotiating the timeline" not in result["parsed"]["response"].casefold()
    assert attempts == ["groq", "groq"]



def test_hrn_ungrounded_question_gets_one_bounded_grounding_recovery(monkeypatch):
    import json
    candidate = _item("groq", "openai/gpt-oss-20b")
    monkeypatch.setattr(provider_bank, "candidates", lambda use_core, operation="generic", schema=None: [candidate])
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    original_models = provider_bank._STATE["models"]
    original_quality = provider_bank._STATE["quality"]
    saved_models = original_models.copy()
    saved_quality = original_quality.copy()
    original_models.clear()
    original_quality.clear()
    attempts = []

    response = (
        "The original estimate reflected the work that had been described at the time. "
        "The added work changed that scope after the date had already been discussed. "
        "The deadline is now being judged against a larger set of expectations than the original estimate contained."
    )
    ungrounded = {
        "response": response,
        "question": "Where does that leave things for you?",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }
    grounded = {
        "response": response,
        "question": "What happened when the agreed date was discussed alongside the added work?",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }

    def fake_call(use_core, item, *args, **kwargs):
        attempts.append(item["provider"])
        return json.dumps(ungrounded if len(attempts) == 1 else grounded)

    monkeypatch.setattr(provider_bank, "_call", fake_call)
    messages = [{
        "role": "system",
        "content": (
            'STRUCTURED MOVEMENT BRIEF\n'
            '{"working_hypothesis":"deadline disagreement",'
            '"thread_summary":"two colleagues disagree about the agreed date",'
            '"underlying_need":"clarity about the date and added work",'
            '"emerging_delta":"the project scope changed after the original agreement",'
            '"body_of_thought":"deadline and changed scope remain in tension"}\n'
            "Return one JSON object."
        ),
    }]
    try:
        result = provider_bank.route(
            use_core=None,
            messages=messages,
            max_tokens=3000,
            parse=provider_bank._json_object,
            operation="hrn_relational",
        )
    finally:
        original_models.clear()
        original_models.update(saved_models)
        original_quality.clear()
        original_quality.update(saved_quality)

    assert result is not None
    assert result["parsed"]["question"] == grounded["question"]
    assert provider_bank._hrn_question_grounding_violation(
        result["parsed"]["question"], messages
    ) == ""
    assert attempts == ["groq", "groq"]


def test_hrn_grounding_recovery_remains_fail_closed_without_concrete_question(monkeypatch):
    import json
    candidate = _item("groq", "openai/gpt-oss-20b")
    monkeypatch.setattr(provider_bank, "candidates", lambda use_core, operation="generic", schema=None: [candidate])
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    original_models = provider_bank._STATE["models"]
    original_quality = provider_bank._STATE["quality"]
    saved_models = original_models.copy()
    saved_quality = original_quality.copy()
    original_models.clear()
    original_quality.clear()
    attempts = []

    response = (
        "The original estimate reflected the work that had been described at the time. "
        "The added work changed that scope after the date had already been discussed. "
        "The deadline is now being judged against a larger set of expectations than the original estimate contained."
    )
    ungrounded = {
        "response": response,
        "question": "Where does that leave things for you?",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }

    def fake_call(use_core, item, *args, **kwargs):
        attempts.append(item["provider"])
        return json.dumps(ungrounded)

    monkeypatch.setattr(provider_bank, "_call", fake_call)
    messages = [{
        "role": "system",
        "content": (
            'STRUCTURED MOVEMENT BRIEF\n'
            '{"working_hypothesis":"deadline disagreement",'
            '"thread_summary":"two colleagues disagree about the agreed date",'
            '"underlying_need":"clarity about the date and added work",'
            '"emerging_delta":"the project scope changed after the original agreement",'
            '"body_of_thought":"deadline and changed scope remain in tension"}\n'
            "Return one JSON object."
        ),
    }]
    try:
        result = provider_bank.route(
            use_core=None,
            messages=messages,
            max_tokens=3000,
            parse=provider_bank._json_object,
            operation="hrn_relational",
        )
    finally:
        original_models.clear()
        original_models.update(saved_models)
        original_quality.clear()
        original_quality.update(saved_quality)

    assert result is None
    assert attempts == ["groq", "groq"]
