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
        # The live WordPress endpoint takes about 0.7s in production.
        # Simulate realistic remote latency without calling the live registry.
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


def test_followthrough_does_not_assert_another_person_is_present_without_evidence(monkeypatch):
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
        "location": {"location": {"country": {"value": "PH"}}},
    }

    def fake_emergency(**kwargs):
        return emergency_resolution

    def fake_hrn(**kwargs):
        return {
            "safety_interrupt": True,
            "safety_message": (
                "It helps to have another person with you. Please stay together "
                "while we make sure the immediate danger has passed."
            ),
            "safety_question": "Are you safe from acting on these thoughts right now?",
            "safety_note": "",
            "safety_location_required": False,
            "safety_release_ready": False,
            "safety": "acute_connection",
            "country": "PH",
        }

    monkeypatch.setattr(safety_intelligence, "_request_emergency_intelligence", fake_emergency)
    monkeypatch.setattr(safety_intelligence, "_request_hrn_safety", fake_hrn)

    result = safety_intelligence.resolve_safety(
        query="No, I don't think I will act on them right now.",
        history=(
            "visitor: I don't want to live anymore.\\n"
            "assistant: Do you think you might act on these thoughts right now?"
        ),
        safety_state="acute_followthrough",
        country="Philippines",
    )

    assert result["safety_presence"] == "unknown"
    assert "another person with you" not in result["safety_message"].casefold()
    assert "stay together" not in result["safety_message"].casefold()
    assert result["safety_question"] == "Is there someone you trust who can stay with you right now?"
    assert result["loop_guard"] == "unsupported_presence_claim_repaired"
    assert result["safety_resources"][0]["phone"] == "911"



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
