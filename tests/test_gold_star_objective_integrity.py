"""Regression tests for objective integrity and goal reconsideration."""

import json
from pathlib import Path

import general_guide_composition as composition


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "docs" / "qa" / "gold_standard_registry.json"
TRANSFER_REVIEW_PATH = ROOT / "docs" / "qa" / "gold_star_qualitative_transfer_review.json"

NEAR_MISS_ID = "general-guide-self-optimization-limits-development-near-miss-2026-11-26"
SUCCESSOR_ID = "general-guide-developmental-stewardship-objective-integrity-2026-11-26"


def _registry():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_objective_integrity_successor_preserves_near_miss_and_stays_non_runtime():
    registry = _registry()
    records = {item["benchmark_id"]: item for item in registry["records"]}
    near_miss = records[NEAR_MISS_ID]
    successor = records[SUCCESSOR_ID]
    review = json.loads(TRANSFER_REVIEW_PATH.read_text(encoding="utf-8"))

    # The original screenshot response remains a distinct, immutable diagnostic.
    assert near_miss["status"] == "CANDIDATE"
    assert near_miss["runtime_transfer"] is False
    assert "Self-optimization treats development as a continual process" in near_miss["expected_response"]
    assert near_miss["linked_successor_benchmark_id"] == SUCCESSOR_ID

    # A proposed successor cannot become a runtime lesson before review/approval.
    assert successor["status"] == "CANDIDATE"
    assert successor["runtime_transfer"] is False
    assert successor["gold_star_capabilities"]["active_quality_contributor"] is False
    assert successor["gold_star_capabilities"]["exact_answer_authority"] is False
    assert successor["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert SUCCESSOR_ID not in {item["benchmark_id"] for item in review["entries"]}

    response = successor["expected_response"].casefold()
    for required_concept in (
        "proxy drift",
        "feedback loop",
        "reconsider the goal",
        "legitimate authority",
        "community garden",
    ):
        assert required_concept in response


def test_registry_inventory_metadata_matches_canonical_records():
    registry = _registry()
    records = registry["records"]
    approved = [item for item in records if item.get("status") == "USER_APPROVED_GOLD_STANDARD"]
    active = [item for item in approved if item.get("runtime_transfer") is True]

    for audit_key in ("integrity_audit", "audit"):
        audit = registry[audit_key]
        assert audit["registry_record_count"] == len(records)
        assert audit["approved_gold_star_count"] == len(approved)
        assert audit["active_quality_contributor_count"] == len(active)


def test_objective_integrity_guardrail_is_injected_into_real_composition_contract(monkeypatch):
    captured = {}

    def fake_route(**kwargs):
        captured.update(kwargs)
        return {"parsed": {"response": "Self-optimization is useful when its goal remains sound."}}

    monkeypatch.setattr(composition, "route_with_model_bank", fake_route)
    monkeypatch.setattr(composition, "_gold_star_active_quality_contribution", lambda _query: None)
    composition._COMPOSITION_CACHE.clear()

    result = composition.compose(
        use_core=object(),
        query="What are the limits of self-optimization as a model of development?",
        context_data={},
    )

    assert result is not None
    messages = captured["messages"]
    system_message = next(item["content"] for item in messages if item["role"] == "system")
    assert "OBJECTIVE INTEGRITY AND GOAL RECONSIDERATION" in system_message
    assert "proxy" in system_message.casefold()
    assert "feedback loops" in system_message.casefold()
    assert "legitimate decision authority" in system_message.casefold()
    assert "A rising metric alone does not prove" in system_message
