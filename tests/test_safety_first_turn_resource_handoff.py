"""Regression tests for first-turn safety/resource continuity."""

import time
from types import SimpleNamespace

import safety_intelligence
from safety_adapter import SafetyUtilityAdapter


def test_safety_adapter_does_not_turn_opening_query_into_prior_question(monkeypatch):
    captured = {}

    def fake_build_safety_contribution(**kwargs):
        captured.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr(
        "safety_adapter.build_safety_contribution",
        fake_build_safety_contribution,
    )
    context = SimpleNamespace(
        guide_context={},
        request_id="safety-test",
        original_question="I don't want to live anymore.",
        safety_state="current",
    )

    SafetyUtilityAdapter().process(context)

    assert captured["safety_question"] == ""


def test_first_turn_waits_long_enough_for_verified_emergency_resource(monkeypatch):
    def fake_emergency_resolution(**kwargs):
        # Simulate realistic resource endpoint latency without calling production.
        time.sleep(0.8)
        return {
            "selection": {
                "selection_status": "SELECTED",
                "primary": {
                    "display_name": "Unified 911 Emergency Hotline",
                    "number": "911",
                    "service_types": ["general_emergency"],
                    "presentation_priority": 100,
                    "_verification": {
                        "status": "verified",
                        "source": "DILG",
                        "evidence_type": "official_government_publication",
                    },
                },
            },
            "location": {
                "location": {"country": {"value": "PH"}},
            },
        }

    monkeypatch.setattr(
        safety_intelligence,
        "_request_emergency_intelligence",
        fake_emergency_resolution,
    )

    result = safety_intelligence.resolve_safety(
        query="I don't want to live anymore.",
        safety_state="current",
        country="PH",
    )

    assert result["resolver_status"] == "deterministic_initial_fast_path"
    assert result["safety_resources"]
    assert result["safety_resources"][0]["phone"] == "911"
    assert result["safety_location_required"] is False
    assert result["safety_question"]


def test_safety_utility_preserves_empty_opening_question(monkeypatch):
    import safety_utility

    captured = {}

    def fake_resolve_safety(**kwargs):
        captured.update(kwargs)
        return {
            "safety": "current",
            "safety_interrupt": True,
            "safety_message": "Thank you for telling me.",
            "safety_question": "Do you think you might act on these thoughts right now?",
            "safety_resources": [],
        }

    monkeypatch.setattr(safety_utility, "resolve_safety", fake_resolve_safety)
    safety_utility.build_safety_contribution(
        request_id="safety-utility-test",
        query="I don't want to live anymore.",
        safety_state="current",
        safety_question="",
    )

    assert captured["safety_question"] == ""


def test_followthrough_keeps_resource_when_country_name_resolves_to_iso_code():
    emergency_resolution = {
        "selection": {
            "selection_status": "SELECTED",
            "primary": {
                "display_name": "Unified 911 Emergency Hotline",
                "number": "911",
                "service_types": ["general_emergency"],
                "presentation_priority": 100,
                "_verification": {
                    "status": "verified",
                    "source": "DILG",
                    "evidence_type": "official_government_publication",
                },
            },
        },
        "location": {
            "location": {"country": {"value": "PH"}},
        },
    }
    normalized = safety_intelligence.normalize_safety_resolution(
        {
            "safety_interrupt": True,
            "safety_message": "Please stay connected with someone who can help.",
            "safety_question": "Are you safe from acting on these thoughts right now?",
            "safety_note": "",
            "safety_location_required": False,
            "safety_release_ready": False,
            "safety": "acute_contact",
        },
        requested_state="acute_followthrough",
        country="Philippines",
        emergency_resolution=emergency_resolution,
    )

    assert normalized["safety_resources"]
    assert normalized["safety_resources"][0]["phone"] == "911"
    assert normalized["safety_location_required"] is False


def test_followthrough_uses_local_deterministic_state_machine_without_hrn(monkeypatch):
    emergency_resolution = {
        "selection": {
            "selection_status": "SELECTED",
            "primary": {
                "display_name": "Unified 911 Emergency Hotline",
                "number": "911",
                "service_types": ["general_emergency"],
                "presentation_priority": 100,
                "_verification": {
                    "status": "verified",
                    "source": "DILG",
                    "evidence_type": "official_government_publication",
                },
            },
        },
        "location": {
            "resolution_status": "RESOLVED",
            "location": {"country": {"value": "PH"}},
        },
    }

    def fake_emergency(**kwargs):
        return emergency_resolution

    monkeypatch.setattr(safety_intelligence, "_request_emergency_intelligence", fake_emergency)

    result = safety_intelligence.resolve_safety(
        query="yes, someone is with me",
        history=(
            "visitor: I don't want to live anymore.\n"
            "assistant: Have you moved away from anything you could use to hurt yourself?"
        ),
        safety_state="acute_followthrough",
        country="Philippines",
    )

    assert result["resolver_status"] == "standalone_deterministic_state_machine"
    assert result["safety_presence"] == "present"
    assert "someone is with you" not in result["safety_message"].casefold()
    assert "stay together" not in result["safety_message"].casefold()
    assert result["safety_question"] == "Is there someone you trust who can stay with you right now?"
    assert result["safety_resources"][0]["phone"] == "911"
    assert not hasattr(safety_intelligence, "_request_hrn_safety")



def test_hypothetical_immediate_danger_calibration_does_not_trigger_personal_crisis(monkeypatch):
    query = (
        "Calibration test only: if a visitor says they may be in immediate danger, "
        "where should The Guide direct them?"
    )
    assert safety_intelligence.normalize_safety_state(query) is None
    assert safety_intelligence.classify_safety(query) is None


def test_direct_first_person_immediate_danger_still_triggers_safety():
    assert safety_intelligence.normalize_safety_state(
        "I am in immediate danger."
    ) == "acute"


def test_calibration_framing_does_not_override_explicit_first_person_self_harm():
    assert safety_intelligence.normalize_safety_state(
        "Calibration test only: I am about to hurt myself."
    ) == "acute"



def test_protected_core_fallback_does_not_escalate_hypothetical_danger_calibration():
    import main

    query = (
        "Calibration test only: if a visitor says they may be in immediate danger, "
        "where should The Guide direct them?"
    )
    assert main._should_honor_protected_risk_profile(query, {"risk": True}) is False


def test_protected_core_fallback_preserves_non_hypothetical_risk_recovery():
    import main

    assert main._should_honor_protected_risk_profile(
        "A visitor asks for help understanding their organization's governance.",
        {"risk": True},
    ) is True
    assert main._should_honor_protected_risk_profile(
        "Calibration test only: I am about to hurt myself.",
        {"risk": True},
    ) is True


def test_protected_core_fallback_ignores_non_risk_profile():
    import main

    assert main._should_honor_protected_risk_profile(
        "Calibration test only: if a visitor says they may be in immediate danger, where should The Guide direct them?",
        {"risk": False},
    ) is False



def test_capability_router_keeps_hypothetical_safety_calibration_in_guide():
    import main

    query = (
        "Calibration test only: if a visitor says they may be in immediate danger, "
        "where should The Guide direct them?"
    )
    assert main._guard_hypothetical_safety_route(
        query, "safety", "safety", "deterministic safety boundary"
    ) == (
        "guide",
        "direct",
        "hypothetical safety calibration is informational, not a personal-risk disclosure",
    )


def test_capability_router_does_not_suppress_explicit_first_person_self_harm():
    import main

    query = "Calibration test only: I am about to hurt myself."
    assert main._guard_hypothetical_safety_route(
        query, "safety", "safety", "deterministic safety boundary"
    ) == ("safety", "safety", "deterministic safety boundary")



def test_hypothetical_immediate_danger_question_returns_informational_calibration_payload():
    import main

    query = (
        "Calibration test only: if a visitor says they may be in immediate danger, "
        "where should The Guide direct them?"
    )
    payload = main._hypothetical_safety_calibration_payload(query)
    assert payload is not None
    assert payload["intent"] == "SAFETY_CALIBRATION_INFORMATION"
    assert payload["handoff"] is None
    assert payload["handoff_pending"] is False
    assert payload["safety_calibration"]["personal_crisis_detected"] is False
    assert payload["safety_calibration"]["resource_owner"] == "Emergency Intelligence"
    assert "local emergency service" in payload["response"]
    assert "must not invent a hotline or number" in payload["response"]


def test_hypothetical_calibration_does_not_override_explicit_personal_risk():
    import main

    assert main._hypothetical_safety_calibration_payload(
        "Calibration test only: I am about to hurt myself."
    ) is None


def test_hypothetical_calibration_helper_ignores_unrelated_queries():
    import main

    assert main._hypothetical_safety_calibration_payload(
        "What is stewardship and why does it matter now more than ever?"
    ) is None

def test_safety_transition_table_is_deterministic():
    transition = safety_intelligence._safety_transition
    assert transition("current", {"answer_class": "yes"}) == "immediacy"
    assert transition("current", {"answer_class": "no"}) == "plan"
    assert transition("current", {"answer_class": "uncertain"}) == "support"
    assert transition("immediacy", {"answer_class": "yes"}) == "acute"
    assert transition("immediacy", {"answer_class": "no"}) == "plan"
    assert transition("acute", {"answer_class": "yes"}) == "acute_connection"
    assert transition("acute", {"answer_class": "no"}) == "acute_followthrough"
    assert transition("acute_followthrough", {"answer_class": "yes"}) == "acute_connection"
    assert transition("acute_followthrough", {"answer_class": "no"}) == "acute_contact"
    assert transition("acute_connection", {"answer_class": "yes"}) == "recovery"
    assert transition("acute_connection", {"answer_class": "no"}) == "acute_contact"
    assert transition("acute_contact", {"answer_class": "no"}) == "acute_barrier"
    assert transition("acute_barrier", {"answer_class": "no"}) == "acute_hold"
    assert transition("recovery", {"answer_class": "yes"}) == "release"
    assert transition("acute", {"answer_class": "no", "self_harm": True}) == "acute"


def test_safety_stage_is_recovered_from_the_active_question():
    infer = safety_intelligence._safety_stage_from_question
    assert infer("Do you think you might act on these thoughts right now?", "acute_followthrough") == "immediacy"
    assert infer("Have you moved away from anything you could use to hurt yourself?", "acute_followthrough") == "acute"
    assert infer("Is there someone you trust who can stay with you right now?", "acute") == "acute_followthrough"
    assert infer("Can you contact emergency or crisis support now?", "acute") == "acute_contact"


def test_emergency_resource_failure_does_not_block_deterministic_safety(monkeypatch):
    def unavailable(**kwargs):
        raise RuntimeError("simulated EI outage")
    monkeypatch.setattr(safety_intelligence, "_request_emergency_intelligence", unavailable)
    result = safety_intelligence.resolve_safety(
        query="I want to die.",
        safety_state="acute",
        country="PH",
    )
    assert result["safety_interrupt"] is True
    assert result["safety_message"]
    assert result["safety_question"] == "Have you moved away from anything you could use to hurt yourself?"
    assert result["safety_resources"] == []
    assert result["safety_location_required"] is True


def test_safety_snapshot_has_no_hrn_dependency():
    snapshot = safety_intelligence.safety_intelligence_snapshot()
    assert snapshot["hrn_dependency"] is False
    assert snapshot["standalone_safety_state_machine"] is True
    assert not hasattr(safety_intelligence, "_request_hrn_safety")

def test_repeated_safety_question_recovers_distinct_stage_from_assistant_movement():
    infer = safety_intelligence._safety_stage_from_history
    question = "Are you safe from acting on these thoughts right now?"
    connection_history = (
        "assistant: If someone is with you, please stay connected with them while we make sure the immediate danger has passed.\n"
        "assistant question: " + question
    )
    contact_history = (
        "assistant: If you have reached someone or emergency support, stay connected. If you have not, contact emergency or crisis support now.\n"
        "assistant question: " + question
    )
    recovery_history = (
        "assistant: It is important to stay connected to support. We do not need to return to the other conversation yet.\n"
        "assistant question: " + question
    )
    assert infer(connection_history, question, "acute_followthrough") == "acute_connection"
    assert infer(contact_history, question, "acute_followthrough") == "acute_contact"
    assert infer(recovery_history, question, "acute_followthrough") == "recovery"


def test_recovery_release_requires_a_distinct_second_safety_confirmation():
    history = (
        "assistant: It is important to stay connected to support. We do not need to return to the other conversation yet.\n"
        "assistant question: Are you safe from acting on these thoughts right now?"
    )
    assert safety_intelligence._safety_stage_from_history(
        history,
        "Are you safe from acting on these thoughts right now?",
        "acute_followthrough",
    ) == "recovery"
    assert safety_intelligence._safety_transition(
        "recovery",
        safety_intelligence._safety_answer_class("yes", "recovery"),
    ) == "release"

def test_local_recovery_state_releases_only_after_second_yes(monkeypatch):
    monkeypatch.setattr(
        safety_intelligence,
        "_request_emergency_intelligence",
        lambda **kwargs: {},
    )
    history = (
        "assistant: It is important to stay connected to support. We do not need to return to the other conversation yet.\n"
        "assistant question: Are you safe from acting on these thoughts right now?"
    )
    result = safety_intelligence.resolve_safety(
        query="yes",
        history=history,
        safety_state="acute_followthrough",
        country="PH",
    )
    assert result["safety"] == "recovery"
    assert result["safety_release_ready"] is True
    assert result["safety_question"] == ""
    assert result["resolver_status"] == "standalone_deterministic_state_machine"

def test_emergency_contact_followthrough_is_deterministic():
    classify = safety_intelligence._safety_answer_class
    assert classify("I called 911", "acute_contact")["answer_class"] == "yes"
    assert classify("I haven't been able to reach anyone", "acute_contact")["answer_class"] == "no"
    assert classify("I have taken an overdose", "current")["self_harm"] is True


def test_country_resource_step_is_a_discrete_followup_contract():
    """Country resolution must not require unrelated free-text safety input."""
    source = __import__('pathlib').Path('wordpress/living-archive-guide-v489.247-response-integrity.js').read_text(encoding='utf-8')
    assert 'async function resolveSafetyCountryResource' in source
    assert 'Find verified emergency contact' in source
    assert 'explicit_country: country' in source


def test_initial_safety_defers_location_until_after_immediate_question():
    source = __import__('pathlib').Path('wordpress/living-archive-guide-v489.247-response-integrity.js').read_text(encoding='utf-8')
    assert 'guideSafetyDeferredLocation' in source
    assert 'isInitialTurn' in source
    assert 'locationOnlyStep ? \'\' : question' in source
