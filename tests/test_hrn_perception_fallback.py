"""Bounded independent-provider fallback for HRN's perception stage."""
import json
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


def _isolate(monkeypatch, candidates):
    monkeypatch.setattr(provider_bank, "select", lambda *args, **kwargs: candidates)
    monkeypatch.setattr(provider_bank, "_sync_shared_state", lambda: None)
    monkeypatch.setattr(provider_bank, "_persist_shared_state", lambda: True)
    monkeypatch.setattr(provider_bank, "_blocked", lambda state, operation=None: False)
    monkeypatch.setattr(provider_bank, "acquire_probe", lambda state: True)
    monkeypatch.setattr(provider_bank, "_failure", lambda *args, **kwargs: None)
    monkeypatch.setattr(provider_bank, "_success", lambda *args, **kwargs: None)
    monkeypatch.setattr(provider_bank, "_state", lambda provider, model: provider_bank.new_state(provider, model))


def test_perception_fast_failures_can_reach_fifth_independent_provider(monkeypatch):
    candidates = [
        _candidate("gemini", "model-a"),
        _candidate("mistral", "model-b"),
        _candidate("workers_ai", "model-c"),
        _candidate("nvidia", "model-d"),
        _candidate("groq", "model-e"),
    ]
    _isolate(monkeypatch, candidates)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def fake_call(use_core, item, messages, max_tokens, schema=None, timeout_override=None):
        calls.append((item["provider"], timeout_override))
        if item["provider"] != "groq" or item["model"] != "model-e":
            durations = {
                "gemini": 0.27,
                "mistral": 1.025,
                "workers_ai": 1.030,
                "nvidia": 1.005,
            }
            clock.value += durations.get(item["provider"], 0.25)
            raise provider_bank.ProviderCallError(
                "simulated fast provider failure",
                item["provider"],
                item["model"],
                429 if item["provider"] == "mistral" else 503,
                category="rate_limited" if item["provider"] == "mistral" else "http_error",
            )
        return json.dumps({"perception": "bounded synthetic result"})

    monkeypatch.setattr(provider_bank, "_quota_guarded_call", fake_call)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "user", "content": "synthetic calibration input"}],
        max_tokens=100,
        parse=provider_bank._json_object,
        operation="hrn_perception",
    )

    assert result is not None
    assert result["provider"] == "groq"
    assert [provider for provider, _ in calls] == ["gemini", "mistral", "workers_ai", "nvidia", "groq"]
    assert all(timeout == provider_bank.HRN_PROVIDER_CALL_TIMEOUT_SECONDS for _, timeout in calls)
    assert provider_bank.HRN_PERCEPTION_FAST_FALLBACK_MAX_CANDIDATES == 4
    assert provider_bank.HRN_PERCEPTION_FAST_FAILURE_WINDOW_SECONDS == 7.0
    assert provider_bank.HRN_PERCEPTION_SLOW_FAILURE_STOP_SECONDS == 4.5
    assert provider_bank.HRN_PROVIDER_CALL_TIMEOUT_SECONDS == 2.5


def test_hrn_relational_prioritizes_half_open_low_latency_workers_ai_before_free_router(monkeypatch):
    candidates = [
        _candidate("openrouter", "openrouter/free"),
        _candidate("mistral", "mistral-small-latest"),
        _candidate("workers_ai", "@cf/zai-org/glm-4.7-flash"),
        _candidate("workers_ai", "@cf/meta/llama-3.3-70b-instruct-fp8-fast"),
        _candidate("nvidia", "nvidia/nemotron-3-super-120b-a12b"),
    ]
    candidates[3]["health_state"] = "half_open"
    _isolate(monkeypatch, candidates)
    calls = []

    def fail_fast(use_core, item, messages, max_tokens, schema=None, timeout_override=None):
        calls.append((item["provider"], item["model"]))
        raise provider_bank.ProviderCallError(
            "simulated independent-lane failure",
            item["provider"],
            item["model"],
            503,
            category="provider_failure",
        )

    monkeypatch.setattr(provider_bank, "_quota_guarded_call", fail_fast)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "user", "content": "STRUCTURED MOVEMENT BRIEF — " + json.dumps({
            "observer_intention": "Understand the change in scope",
            "observer_contrast": "The agreed deadline remained while scope changed",
            "observer_so_what": "Expectations may no longer match",
            "observer_delta": "The conversation moved from delivery to fairness",
            "observer_horizon": "The moment the scope changed",
            "observer_next_intention": "What the colleague understood the change to mean",
        })}],
        max_tokens=600,
        parse=provider_bank._json_object,
        operation="hrn_relational",
    )

    assert result is None
    assert calls[0] == ("workers_ai", "@cf/meta/llama-3.3-70b-instruct-fp8-fast")


def test_perception_does_not_spend_turn_budget_on_fallback_after_slow_failure(monkeypatch):
    candidates = [_candidate("groq", "model-a"), _candidate("nvidia", "model-b")]
    _isolate(monkeypatch, candidates)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def slow_failure(use_core, item, messages, max_tokens, schema=None, timeout_override=None):
        calls.append(item["provider"])
        clock.value += 5.0
        raise RuntimeError("simulated slow timeout")

    monkeypatch.setattr(provider_bank, "_quota_guarded_call", slow_failure)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "user", "content": "synthetic calibration input"}],
        max_tokens=100,
        parse=provider_bank._json_object,
        operation="hrn_perception",
    )

    assert result is None
    assert calls == ["groq"]



def test_empty_movement_brief_is_input_failure_not_provider_quality_failure():
    reason = "hrn_relational question-surface contract violation: question-grounding contract violation: movement brief has no concrete question anchors"
    assert provider_bank._is_movement_brief_input_failure("hrn_relational", reason)
    assert not provider_bank._is_movement_brief_input_failure(
        "hrn_relational",
        "question-grounding contract violation: question does not name a concrete detail from the movement brief",
    )
    assert not provider_bank._is_movement_brief_input_failure(
        "general_guide_composition",
        reason,
    )



def test_groq_bounded_call_disables_sdk_retries(monkeypatch):
    from types import SimpleNamespace

    options = []
    call_kwargs = {}

    class FakeClient:
        def __init__(self):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=self.create)
            )

        def with_options(self, **kwargs):
            options.append(kwargs)
            return self

        def create(self, **kwargs):
            call_kwargs.update(kwargs)
            message = SimpleNamespace(content='{"perception":"bounded result"}')
            usage = SimpleNamespace(completion_tokens=17)
            return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)

    use_core = SimpleNamespace(groq_client=FakeClient())
    result = provider_bank._groq(
        use_core,
        "openai/gpt-oss-120b",
        [{"role": "user", "content": "synthetic calibration input"}],
        100,
        schema=None,
        timeout=1.0,
    )

    assert result == '{"perception":"bounded result"}'
    assert result.completion_tokens == 17
    assert options == [{"timeout": 1.0, "max_retries": 0}]
    assert call_kwargs["max_completion_tokens"] == 100


def test_relational_composition_recovers_forbidden_formulaic_connective(monkeypatch):
    candidates = [_candidate("groq", "model-a")]
    _isolate(monkeypatch, candidates)

    brief = {
        "observer_intention": "You both want the recurring argument to change.",
        "observer_contrast": "The same exchange keeps returning after something from the past is raised.",
        "observer_so_what": "Both want improvement, but the repeated exchange continues.",
        "observer_delta": "The conversation moves from the past issue to one partner feeling blamed.",
        "observer_horizon": "The moment something from the past is brought up.",
        "observer_next_intention": "Notice what is said just before blame enters the exchange.",
    }
    messages = [{
        "role": "user",
        "content": "STRUCTURED MOVEMENT BRIEF — " + json.dumps(brief),
    }]
    rejected = {
        "response": (
            "You both say you want the argument to change, yet the same exchange keeps returning. "
            "This opens the possibility of changing the conversation into a question of blame. "
            "The words that start this shift are clear in your description, though their meaning to each of you remains unknown."
        ),
        "question": "What is usually said just before one of you brings up something from the past?",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }
    repaired = {
        "response": (
            "You both say you want the argument to change, yet the same exchange keeps returning. "
            "When something from the past is raised, one of you feels blamed, and the conversation moves away from the wish to improve. "
            "That sequence is clear in what you described, though it does not establish what either of you intends."
        ),
        "question": "What is usually said just before one of you brings up something from the past?",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }
    calls = []

    def fake_call(use_core, item, call_messages, max_tokens, schema=None, timeout_override=None):
        calls.append(call_messages)
        return json.dumps(rejected if len(calls) == 1 else repaired)

    monkeypatch.setattr(provider_bank, "_quota_guarded_call", fake_call)
    result = provider_bank.route(
        use_core=None,
        messages=messages,
        max_tokens=600,
        parse=provider_bank._json_object,
        operation="hrn_relational",
    )
    assert result is not None
    assert len(calls) == 2
    assert result["parsed"]["response"] == repaired["response"]
    assert "opens the possibility of" not in result["parsed"]["response"].casefold()


def test_relational_composition_still_fails_closed_when_voice_repair_fails(monkeypatch):
    candidates = [_candidate("groq", "model-a")]
    _isolate(monkeypatch, candidates)
    rejected = {
        "response": (
            "You both say you want the argument to change, yet the same exchange keeps returning. "
            "This opens the possibility of changing the conversation into a question of blame. "
            "The words that start this shift are clear in your description, though their meaning to each of you remains unknown."
        ),
        "question": "What is usually said just before one of you brings up something from the past?",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }
    calls = []

    def fake_call(use_core, item, call_messages, max_tokens, schema=None, timeout_override=None):
        calls.append(call_messages)
        return json.dumps(rejected)

    monkeypatch.setattr(provider_bank, "_quota_guarded_call", fake_call)
    result = provider_bank.route(
        use_core=None,
        messages=[{
            "role": "user",
            "content": "STRUCTURED MOVEMENT BRIEF — " + json.dumps({
                "observer_intention": "You both want the recurring argument to change.",
                "observer_contrast": "The same exchange keeps returning after something from the past is raised.",
                "observer_so_what": "Both want improvement, but the repeated exchange continues.",
                "observer_delta": "The conversation moves from the past issue to one partner feeling blamed.",
                "observer_horizon": "The moment something from the past is brought up.",
                "observer_next_intention": "Notice what is said just before blame enters the exchange.",
            }),
        }],
        max_tokens=600,
        parse=provider_bank._json_object,
        operation="hrn_relational",
    )
    assert result is None
    assert len(calls) == 2


def test_relational_composition_recovers_prescriptive_response_language(monkeypatch):
    candidates = [_candidate("groq", "model-a")]
    _isolate(monkeypatch, candidates)
    brief = {
        "observer_intention": "You both want the recurring argument to change.",
        "observer_contrast": "The same exchange keeps returning after something from the past is raised.",
        "observer_so_what": "Both want improvement, but the repeated exchange continues.",
        "observer_delta": "The conversation moves from the past issue to one partner feeling blamed.",
        "observer_horizon": "The moment something from the past is brought up.",
        "observer_next_intention": "Notice what is said just before blame enters the exchange.",
    }
    rejected = {
        "response": (
            "You both say you want the argument to change, yet the same exchange keeps returning. "
            "You should focus on the moment the past is raised and try to keep the conversation from becoming about blame. "
            "The words that start this shift are clear in your description, though their meaning to each of you remains unknown."
        ),
        "question": "What is usually said just before one of you brings up something from the past?",
        "rest": False, "use_resource": False, "resource_intro": "",
    }
    repaired = {
        "response": (
            "You both say you want the argument to change, yet the same exchange keeps returning. "
            "When something from the past is raised, one of you feels blamed, and the conversation moves away from the wish to improve. "
            "That sequence is clear in what you described, though it does not establish what either of you intends."
        ),
        "question": "What is usually said just before one of you brings up something from the past?",
        "rest": False, "use_resource": False, "resource_intro": "",
    }
    calls = []
    def fake_call(use_core, item, call_messages, max_tokens, schema=None, timeout_override=None):
        calls.append(call_messages)
        return json.dumps(rejected if len(calls) == 1 else repaired)
    monkeypatch.setattr(provider_bank, "_quota_guarded_call", fake_call)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role":"user","content":"STRUCTURED MOVEMENT BRIEF — "+json.dumps(brief)}],
        max_tokens=600,
        parse=provider_bank._json_object,
        operation="hrn_relational",
    )
    assert result is not None
    assert len(calls) == 2
    assert "you should" not in result["parsed"]["response"].casefold()
    assert "try to keep" not in result["parsed"]["response"].casefold()


def test_relational_composition_recovers_observed_generic_metaphor(monkeypatch):
    candidates = [_candidate("groq", "model-a")]
    _isolate(monkeypatch, candidates)
    brief = {
        "observer_intention": "You both want the recurring argument to change.",
        "observer_contrast": "The same exchange keeps returning after something from the past is raised.",
        "observer_so_what": "Both want improvement, but the repeated exchange continues.",
        "observer_delta": "The conversation moves from the past issue to one partner feeling blamed.",
        "observer_horizon": "The moment something from the past is brought up.",
        "observer_next_intention": "Notice what is said just before blame enters the exchange.",
    }
    rejected = {
        "response": (
            "A useful distinction is that the repeated argument is a shared signal. "
            "You are speaking different languages, and this can become a win-lose fight. "
            "That sequence is clear in what you described, though it does not establish what either of you intends."
        ),
        "question": "What is usually said just before one of you brings up something from the past?",
        "rest": False, "use_resource": False, "resource_intro": "",
    }
    repaired = {
        "response": (
            "You both say you want the argument to change, yet the same exchange keeps returning. "
            "When something from the past is raised, one of you feels blamed, and the conversation moves away from the wish to improve. "
            "That sequence is clear in what you described, though it does not establish what either of you intends."
        ),
        "question": "What is usually said just before one of you brings up something from the past?",
        "rest": False, "use_resource": False, "resource_intro": "",
    }
    calls = []
    def fake_call(use_core, item, call_messages, max_tokens, schema=None, timeout_override=None):
        calls.append(call_messages)
        return json.dumps(rejected if len(calls) == 1 else repaired)
    monkeypatch.setattr(provider_bank, "_quota_guarded_call", fake_call)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role":"user","content":"STRUCTURED MOVEMENT BRIEF — "+json.dumps(brief)}],
        max_tokens=600,
        parse=provider_bank._json_object,
        operation="hrn_relational",
    )
    assert result is not None
    assert len(calls) == 2
    assert "shared signal" not in result["parsed"]["response"].casefold()
    assert "speaking different languages" not in result["parsed"]["response"].casefold()


def test_hrn_grounding_rejects_abstract_only_relationship_question():
    import json
    brief = {
        "observer_intention": "My partner and I keep having the same argument, even though we both say we want things to improve.",
        "observer_contrast": "No distinct contrast was established in this round.",
        "observer_so_what": "The current understanding has not yet yielded a distinct new perspective.",
        "observer_next_intention": "Notice the point where the familiar exchange returns.",
    }
    violation = provider_bank._hrn_question_grounding_violation(
        "Where do you notice that distinction most clearly in the relationship?",
        [{"role":"user","content":"STRUCTURED MOVEMENT BRIEF — "+json.dumps(brief)}],
    )
    assert violation == "question-grounding contract violation: question does not name a concrete detail from the movement brief"


def test_hrn_grounding_accepts_a_concrete_detail_from_the_actual_exchange():
    import json
    brief = {
        "observer_intention": "My partner and I keep having the same argument, even though we both say we want things to improve.",
        "observer_contrast": "The argument usually starts when one of us brings up something from the past.",
        "observer_so_what": "One partner then feels blamed.",
        "observer_next_intention": "Notice what is said just before blame enters the exchange.",
    }
    violation = provider_bank._hrn_question_grounding_violation(
        "What is usually said just before one of you brings up something from the past?",
        [{"role":"user","content":"STRUCTURED MOVEMENT BRIEF — "+json.dumps(brief)}],
    )
    assert violation == ""


def test_relational_composition_recovers_observed_rhythm_and_landing_metaphors(monkeypatch):
    candidates = [_candidate("groq", "model-a")]
    _isolate(monkeypatch, candidates)
    brief = {
        "observer_intention": "You both want the recurring argument to change.",
        "observer_contrast": "The same exchange keeps returning after something from the past is raised.",
        "observer_so_what": "Both want improvement, but the repeated exchange continues.",
        "observer_delta": "The conversation moves from the past issue to one partner feeling blamed.",
        "observer_horizon": "The moment something from the past is brought up.",
        "observer_next_intention": "Notice what is said just before blame enters the exchange.",
    }
    rejected = {
        "response": (
            "There is a specific friction when the words about wanting change do not match the rhythm of the argument itself. "
            "You are both holding the intention to improve, yet the interaction keeps landing in the same place, which suggests the desire is not translating into a different way of meeting each other in that moment."
        ),
        "question": "What is usually said just before one of you brings up something from the past?",
        "rest": False, "use_resource": False, "resource_intro": "",
    }
    repaired = {
        "response": (
            "You both say you want the argument to change, yet the same exchange keeps returning. "
            "When something from the past is raised, one of you feels blamed, and the conversation moves away from the wish to improve. "
            "That sequence is clear in what you described, though it does not establish what either of you intends."
        ),
        "question": "What is usually said just before one of you brings up something from the past?",
        "rest": False, "use_resource": False, "resource_intro": "",
    }
    calls = []
    def fake_call(use_core, item, call_messages, max_tokens, schema=None, timeout_override=None):
        calls.append(call_messages)
        return json.dumps(rejected if len(calls) == 1 else repaired)
    monkeypatch.setattr(provider_bank, "_quota_guarded_call", fake_call)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role":"user","content":"STRUCTURED MOVEMENT BRIEF — "+json.dumps(brief)}],
        max_tokens=600,
        parse=provider_bank._json_object,
        operation="hrn_relational",
    )
    assert result is not None
    assert len(calls) == 2
    for phrase in ("specific friction","rhythm of the argument","keeps landing in the same place","desire is not translating","different way of meeting each other"):
        assert phrase not in result["parsed"]["response"].casefold()


def test_hrn_contract_recovery_compacts_context_without_losing_movement_brief():
    brief = {
        "observer_intention": "Both partners say they want the argument to change.",
        "observer_contrast": "The same argument keeps returning.",
        "observer_so_what": "The stated wish to improve has not changed the recurring exchange.",
    }
    source = (
        "Repeated long history. " * 900
        + "\nSTRUCTURED MOVEMENT BRIEF — "
        + json.dumps(brief)
        + "\nHRN VISITOR-FACING LANGUAGE CONTRACT: Be concrete, non-prescriptive, and do not infer motives."
    )
    recovery = provider_bank._compact_hrn_contract_recovery_messages(
        [{"role": "user", "content": source}],
        '{"response":"Rejected draft.","question":"What usually happens first?"}',
        "Correct the missing required response field and preserve the visitor's context.",
    )
    assert len(recovery) == 2
    assert len(recovery[1]["content"]) < len(source)
    assert "STRUCTURED MOVEMENT BRIEF" in recovery[1]["content"]
    assert '"observer_intention"' in recovery[1]["content"]
    assert "HRN VISITOR-FACING LANGUAGE CONTRACT" in recovery[1]["content"]
    assert "Rejected draft" in recovery[1]["content"]
    assert "missing required response field" in recovery[1]["content"]


def test_legacy_provider_timeout_cooldown_is_bounded_for_recovery(monkeypatch):
    now = 1000.0
    monkeypatch.setattr(provider_bank.time, "time", lambda: now)
    recently_failed = {
        "provider": "workers_ai",
        "model": "@cf/example/model",
        "state": "open",
        "category": "provider_failure",
        "last_error": "The read operation timed out",
        "last_failure": 990.0,
        "cooldown_until": 1290.0,
        "quarantine_until": 0.0,
        "probe_in_flight": False,
    }
    assert provider_bank._blocked(recently_failed) is True
    assert recently_failed["cooldown_until"] == 1010.0

    recovered = dict(recently_failed)
    recovered["state"] = "open"
    recovered["last_failure"] = 970.0
    recovered["cooldown_until"] = 1270.0
    assert provider_bank._blocked(recovered) is False
    assert recovered["state"] == "half_open"


def test_provider_rate_limit_cooldown_is_not_shortened_by_timeout_policy(monkeypatch):
    now = 1000.0
    monkeypatch.setattr(provider_bank.time, "time", lambda: now)
    rate_limited = {
        "provider": "mistral",
        "model": "mistral-small-latest",
        "state": "open",
        "category": "rate_limited",
        "last_error": "HTTP 429 rate limit",
        "last_failure": 990.0,
        "cooldown_until": 1090.0,
        "quarantine_until": 0.0,
        "probe_in_flight": False,
    }
    assert provider_bank._blocked(rate_limited) is True
    assert rate_limited["cooldown_until"] == 1090.0


def test_hrn_relational_completion_budget_preserves_question_under_second_stage(monkeypatch):
    candidates = [_candidate("groq", "model-a")]
    _isolate(monkeypatch, candidates)
    brief = {
        "observer_intention": "Both partners say they want the recurring argument to change.",
        "observer_contrast": "The same exchange keeps returning.",
        "observer_so_what": "The stated wish to improve has not changed the repeated argument.",
        "observer_delta": "One partner feels blamed when something from the past is raised.",
        "observer_horizon": "The moment the past is brought up.",
        "observer_next_intention": "What is said just before the past is raised.",
    }
    response = (
        "Both of you say you want the argument to change, yet the same exchange keeps returning. "
        "When something from the past is raised, one of you feels blamed. "
        "The wish to improve is present, but the exchange still returns to that point; "
        "what either of you intends remains unknown."
    )
    output = {
        "response": response,
        "question": "What usually happens just before one of you brings up something from the past?",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }
    token_limits = []

    def fake_call(use_core, item, call_messages, max_tokens, schema=None, timeout_override=None):
        token_limits.append(max_tokens)
        return json.dumps(output)

    monkeypatch.setattr(provider_bank, "_quota_guarded_call", fake_call)
    result = provider_bank.route(
        use_core=None,
        messages=[{
            "role": "user",
            "content": "STRUCTURED MOVEMENT BRIEF — " + json.dumps(brief),
        }],
        max_tokens=600,
        parse=provider_bank._json_object,
        operation="hrn_relational",
    )
    assert result is not None
    assert token_limits == [600]
    assert provider_bank.HRN_RELATIONAL_MAX_COMPLETION_TOKENS == 700
    assert provider_bank.OPERATION_TOKEN_FLOORS["hrn_relational"] == 600


def test_hrn_unclassified_embedded_question_failure_skips_same_model_schema_retry(monkeypatch):
    candidates = [
        _candidate("nvidia", "model-a"),
        _candidate("groq", "model-b"),
    ]
    _isolate(monkeypatch, candidates)
    brief = {
        "observer_intention": "Both partners say they want the recurring argument to change.",
        "observer_contrast": "The same exchange keeps returning.",
        "observer_so_what": "The stated wish to improve has not changed the repeated argument.",
        "observer_delta": "One partner feels blamed when something from the past is raised.",
        "observer_horizon": "The moment the past is brought up.",
        "observer_next_intention": "What is said just before the past is raised.",
    }
    rejected = {
        "response": (
            "Both of you say you want the argument to change, yet the same exchange keeps returning. "
            "When something from the past is raised, one of you feels blamed. "
            "What usually happens just before one of you brings up the past?"
        ),
        "question": "What usually happens just before one of you brings up something from the past?",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }
    repaired = {
        "response": (
            "Both of you say you want the argument to change, yet the same exchange keeps returning. "
            "When something from the past is raised, one of you feels blamed. "
            "The wish to improve is present, but what either of you intends remains unknown."
        ),
        "question": "What usually happens just before one of you brings up something from the past?",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }
    calls = []

    def fake_call(use_core, item, call_messages, max_tokens, schema=None, timeout_override=None):
        calls.append(item["provider"])
        return json.dumps(rejected if len(calls) == 1 else repaired)

    monkeypatch.setattr(provider_bank, "_quota_guarded_call", fake_call)
    result = provider_bank.route(
        use_core=None,
        messages=[{
            "role": "user",
            "content": "STRUCTURED MOVEMENT BRIEF — " + json.dumps(brief),
        }],
        max_tokens=600,
        parse=provider_bank._json_object,
        operation="hrn_relational",
    )
    assert result is not None
    assert calls == ["nvidia", "groq"]

def test_hrn_surface_policy_distinguishes_reported_words_from_advice():
    reported_observation = (
        "Both of you say you want the argument to change, yet the same exchange keeps returning. "
        "When something from the past is raised, one of you feels blamed. "
        "The wish to improve is present, but what either of you intends remains unknown."
    )
    direct_advice = "You should say what you need before the argument starts."
    assert provider_bank._hrn_surface_language_violation(reported_observation) == ""
    assert provider_bank._hrn_surface_language_violation(direct_advice) != ""

def test_perception_fallback_can_try_an_alternate_model_from_same_provider(monkeypatch):
    """A model-level timeout must not hide a healthy sibling model."""
    candidates = [
        _candidate("groq", "model-a"),
        _candidate("nvidia", "gemma-model"),
        _candidate("nvidia", "nemotron-model"),
        _candidate("mistral", "model-d"),
    ]
    _isolate(monkeypatch, candidates)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def fake_call(use_core, item, messages, max_tokens, schema=None, timeout_override=None):
        calls.append((item["provider"], item["model"]))
        if item["model"] == "nemotron-model":
            return json.dumps({"perception": "bounded synthetic result"})
        clock.value += 0.25
        raise provider_bank.ProviderCallError(
            "simulated model-specific failure",
            item["provider"],
            item["model"],
            503,
            category="http_error",
        )

    monkeypatch.setattr(provider_bank, "_quota_guarded_call", fake_call)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "user", "content": "synthetic calibration input"}],
        max_tokens=100,
        parse=provider_bank._json_object,
        operation="hrn_perception",
    )

    assert result is not None
    assert result["provider"] == "nvidia"
    assert result["model"] == "nemotron-model"
    assert calls == [
        ("groq", "model-a"),
        ("nvidia", "gemma-model"),
        ("nvidia", "nemotron-model"),
    ]

def test_relational_fallback_prioritizes_sibling_after_one_independent_lane(monkeypatch):
    """Try one independent provider, then a sibling model, within the existing 7s budget."""
    candidates = [
        _candidate("nvidia", "gemma-model"),
        _candidate("openrouter", "model-b"),
        _candidate("mistral", "model-c"),
        _candidate("workers_ai", "model-d"),
        _candidate("nvidia", "nemotron-model"),
    ]
    _isolate(monkeypatch, candidates)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def fake_call(use_core, item, messages, max_tokens, schema=None, timeout_override=None):
        calls.append((item["provider"], item["model"]))
        if item["model"] == "nemotron-model":
            return json.dumps({
                "response": "You both say you want things to improve, but the same argument keeps returning. When it begins again, the conversation can move away from what happened and toward whether the past should be reopened. I do not know either person's intention, so I will stay with the sequence you described.",
                "question": "What usually happens just before the argument starts again?",
                "rest": False,
                "use_resource": False,
                "resource_intro": "",
            })
        clock.value += 1.3
        raise provider_bank.ProviderCallError(
            "simulated clustered provider failure",
            item["provider"],
            item["model"],
            429 if item["provider"] in {"openrouter", "mistral"} else 503,
            category="rate_limited" if item["provider"] in {"openrouter", "mistral"} else "http_error",
        )

    monkeypatch.setattr(provider_bank, "_quota_guarded_call", fake_call)
    result = provider_bank.route(
        use_core=None,
        messages=[{
            "role": "user",
            "content": (
                'SOURCE CONTRACT FOR THIS RESPONSE: {"mode":"answer","schema":"v1"}\n'
                'STRUCTURED MOVEMENT BRIEF — compose from this interpretation:\n'
                '{"thread_summary":"Both partners say they want things to improve, but the same argument keeps returning.",'
                '"working_hypothesis":"The conversation shifts away from the specific incident when the past is raised.",'
                '"perspective_delta":"The discussion moves from what happened to whether the visitor may still feel hurt."}'
            ),
        }],
        max_tokens=250,
        parse=provider_bank._json_object,
        operation="hrn_relational",
    )

    assert result is not None
    assert result["provider"] == "nvidia"
    assert result["model"] == "nemotron-model"
    assert calls == [
        ("nvidia", "gemma-model"),
        ("openrouter", "model-b"),
        ("nvidia", "nemotron-model"),
    ]
    assert provider_bank.HRN_RELATIONAL_FAST_FALLBACK_MAX_CANDIDATES == 5
    assert provider_bank.HRN_RELATIONAL_FAST_FAILURE_WINDOW_SECONDS == 7.0




def test_relational_fallback_uses_recently_successful_nemotron_first(monkeypatch):
    """A known-live independent lane must be attempted before slower candidates."""
    candidates = [
        _candidate("groq", "qwen/qwen3.8-27b"),
        _candidate("openrouter", "openrouter/free"),
        _candidate("nvidia", "google/gemma-4-31b-it"),
        _candidate("mistral", "mistral-small-latest"),
        _candidate("nvidia", "nvidia/nemotron-3.5-lightning-30b-a3b"),
        _candidate("workers_ai", "@cf/zai-org/glm-4.7-flash"),
    ]
    _isolate(monkeypatch, candidates)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def fake_call(use_core, item, messages, max_tokens, schema=None, timeout_override=None):
        calls.append((item["provider"], item["model"]))
        if item["provider"] == "nvidia" and item["model"] == "nvidia/nemotron-3.5-lightning-30b-a3b":
            return json.dumps({
                "response": "You both say you want things to improve, yet the same argument keeps returning. From what you described, the conversation can move away from the incident itself and toward whether you are allowed to still feel hurt. I cannot know either person’s intention, so I will stay with the sequence you noticed.",
                "question": "What usually happens just before the argument starts again?",
                "rest": False,
                "use_resource": False,
                "resource_intro": "",
            })
        clock.value += 0.35
        raise provider_bank.ProviderCallError(
            "simulated fast failure",
            item["provider"],
            item["model"],
            429 if item["provider"] == "openrouter" else 503,
            category="rate_limited" if item["provider"] == "openrouter" else "http_error",
        )

    monkeypatch.setattr(provider_bank, "_quota_guarded_call", fake_call)
    result = provider_bank.route(
        use_core=None,
        messages=[{
            "role": "user",
            "content": (
                'SOURCE CONTRACT FOR THIS RESPONSE: {"mode":"answer","schema":"v1"}\n'
                'STRUCTURED MOVEMENT BRIEF — compose from this interpretation:\n'
                '{"thread_summary":"The same argument keeps returning.",'
                '"working_hypothesis":"The discussion shifts from the incident to whether it can be mentioned.",'
                '"perspective_delta":"The visitor wants to discuss hurt without being blamed."}'
            ),
        }],
        max_tokens=250,
        parse=provider_bank._json_object,
        operation="hrn_relational",
    )

    assert result is not None
    assert result["provider"] == "nvidia"
    assert result["model"] == "nvidia/nemotron-3.5-lightning-30b-a3b"
    assert calls == [
        ("nvidia", "nvidia/nemotron-3.5-lightning-30b-a3b"),
    ]



def test_provider_timeout_circuit_is_isolated_by_operation():
    """A timeout in perception must not suppress a model for relational composition."""
    import time

    state = provider_bank.new_state("nvidia", "nvidia/nemotron-3.5-lightning-30b-a3b")
    state.update({
        "state": "open",
        "category": "provider_failure",
        "last_error": "request timed out after 2.0 seconds",
        "last_failure": time.time(),
        "cooldown_until": time.time() + 300,
        "quarantine_until": 0.0,
        "last_operation": "hrn_perception",
    })

    assert provider_bank._blocked_for_operation(state, "hrn_relational") is False
    assert provider_bank._blocked_for_operation(state, "hrn_perception") is True



def test_perception_tries_one_fallback_after_slow_but_budgeted_failure(monkeypatch):
    candidates = [_candidate("groq", "model-a"), _candidate("nvidia", "model-b")]
    _isolate(monkeypatch, candidates)

    class Clock:
        value = 0.0

    clock = Clock()
    monkeypatch.setattr(provider_bank.time, "monotonic", lambda: clock.value)
    calls = []

    def fake_call(use_core, item, messages, max_tokens, schema=None, timeout_override=None):
        calls.append(item["provider"])
        if item["provider"] == "groq":
            clock.value += 3.5
            raise RuntimeError("simulated slow first-provider failure")
        return json.dumps({"perception": "bounded synthetic result"})

    monkeypatch.setattr(provider_bank, "_quota_guarded_call", fake_call)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "user", "content": "synthetic calibration input"}],
        max_tokens=100,
        parse=provider_bank._json_object,
        operation="hrn_perception",
    )

    assert result is not None
    assert result["provider"] == "nvidia"
    assert calls == ["groq", "nvidia"]
    assert clock.value == 3.5


def test_recently_successful_nemotron_lightning_is_first_for_perception(monkeypatch):
    candidates = [
        _candidate("nvidia", "nvidia/nemotron-3-super-120b-a12b"),
        _candidate("workers_ai", "@cf/google/gemma-4-26b-a4b-it"),
        _candidate("nvidia", "nvidia/nemotron-3.5-lightning-30b-a3b"),
    ]
    _isolate(monkeypatch, candidates)
    calls = []

    def fake_call(use_core, item, messages, max_tokens, schema=None, timeout_override=None):
        calls.append((item["provider"], item["model"]))
        return json.dumps({"perception": "bounded synthetic result"})

    monkeypatch.setattr(provider_bank, "_quota_guarded_call", fake_call)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "user", "content": "synthetic calibration input"}],
        max_tokens=100,
        parse=provider_bank._json_object,
        operation="hrn_perception",
    )

    assert result is not None
    assert result["provider"] == "nvidia"
    assert result["model"] == "nvidia/nemotron-3.5-lightning-30b-a3b"
    assert calls[0] == ("nvidia", "nvidia/nemotron-3.5-lightning-30b-a3b")


def test_recently_successful_nemotron_lightning_is_first_for_relational(monkeypatch):
    candidates = [
        _candidate("nvidia", "nvidia/nemotron-3-super-120b-a12b"),
        _candidate("workers_ai", "@cf/google/gemma-4-26b-a4b-it"),
        _candidate("nvidia", "nvidia/nemotron-3.5-lightning-30b-a3b"),
    ]
    _isolate(monkeypatch, candidates)
    calls = []

    def fake_call(use_core, item, messages, max_tokens, schema=None, timeout_override=None):
        calls.append((item["provider"], item["model"]))
        raise provider_bank.ProviderCallError(
            "simulated fast provider failure",
            item["provider"],
            item["model"],
            503,
            category="http_error",
        )

    monkeypatch.setattr(provider_bank, "_quota_guarded_call", fake_call)
    result = provider_bank.route(
        use_core=None,
        messages=[{
            "role": "user",
            "content": "STRUCTURED MOVEMENT BRIEF — " + json.dumps({
                "observer_intention": "A friendship matters to the visitor.",
                "observer_contrast": "The visitor fears that an honest conversation could change the friendship.",
                "observer_so_what": "The wish to speak and the fear of change are both explicit.",
                "observer_delta": "No further distinction has been established.",
                "observer_horizon": "The conversation with the friend.",
                "observer_next_intention": "Explore what the visitor wants understood.",
            }),
        }],
        max_tokens=100,
        parse=provider_bank._json_object,
        operation="hrn_relational",
    )

    assert result is None
    assert calls
    assert calls[0] == ("nvidia", "nvidia/nemotron-3.5-lightning-30b-a3b")


def test_half_open_nemotron_lightning_does_not_leapfrog_healthy_candidate(monkeypatch):
    candidates = [
        _candidate("workers_ai", "@cf/google/gemma-4-26b-a4b-it"),
        _candidate("nvidia", "nvidia/nemotron-3.5-lightning-30b-a3b"),
    ]
    candidates[1]["health_state"] = "half_open"
    _isolate(monkeypatch, candidates)
    calls = []

    def fake_call(use_core, item, messages, max_tokens, schema=None, timeout_override=None):
        calls.append((item["provider"], item["model"]))
        if item["provider"] == "workers_ai":
            return json.dumps({"perception": "bounded synthetic result"})
        raise AssertionError("half-open candidate should not run before the healthy lane")

    monkeypatch.setattr(provider_bank, "_quota_guarded_call", fake_call)
    result = provider_bank.route(
        use_core=None,
        messages=[{"role": "user", "content": "synthetic calibration input"}],
        max_tokens=100,
        parse=provider_bank._json_object,
        operation="hrn_perception",
    )

    assert result is not None
    assert calls[0] == ("workers_ai", "@cf/google/gemma-4-26b-a4b-it")
