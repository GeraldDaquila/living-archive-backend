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
