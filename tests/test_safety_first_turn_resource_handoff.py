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
