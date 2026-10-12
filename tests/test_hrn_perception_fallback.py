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
    monkeypatch.setattr(provider_bank, "_blocked", lambda state: False)
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
    assert provider_bank.HRN_PERCEPTION_SLOW_FAILURE_STOP_SECONDS == 2.5
    assert provider_bank.HRN_PROVIDER_CALL_TIMEOUT_SECONDS == 2.0


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
        clock.value += 3.5
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


def test_hrn_relational_uses_small_completion_budget_for_second_stage(monkeypatch):
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
    assert token_limits == [250]
    assert provider_bank.HRN_RELATIONAL_MAX_COMPLETION_TOKENS == 250


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
    assert provider_bank._hrn_surface_language_violation(direct_advice) == "prescriptive-language"
