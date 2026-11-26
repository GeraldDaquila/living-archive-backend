"""Regression tests for objective integrity and goal reconsideration."""

import json
from pathlib import Path

import general_guide_composition as composition


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "docs" / "qa" / "gold_standard_registry.json"
TRANSFER_REVIEW_PATH = ROOT / "docs" / "qa" / "gold_star_qualitative_transfer_review.json"
MAP_PATH = ROOT / "docs" / "qa" / "gold_star_transferability_map.json"

NEAR_MISS_ID = "general-guide-self-optimization-limits-development-near-miss-2026-11-26"
SUCCESSOR_ID = "general-guide-developmental-stewardship-objective-integrity-2026-11-26"


def _registry():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_approved_objective_integrity_successor_preserves_near_miss_and_bounded_authority():
    registry = _registry()
    records = {item["benchmark_id"]: item for item in registry["records"]}
    near_miss = records[NEAR_MISS_ID]
    successor = records[SUCCESSOR_ID]
    review = json.loads(TRANSFER_REVIEW_PATH.read_text(encoding="utf-8"))
    transfer_map = json.loads(MAP_PATH.read_text(encoding="utf-8"))

    # The original screenshot response remains a distinct, immutable diagnostic.
    assert near_miss["status"] == "CANDIDATE"
    assert near_miss["runtime_transfer"] is False
    assert "Self-optimization treats development as a continual process" in near_miss["expected_response"]
    assert near_miss["linked_successor_benchmark_id"] == SUCCESSOR_ID
    assert near_miss["successor_state"] == "SUCCESSOR_APPROVED_AS_SEPARATE_GOLD_STAR"

    # The approved successor contributes only its bounded structural discipline.
    assert successor["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert successor["runtime_transfer"] is True
    assert successor["gold_star_capabilities"]["active_quality_contributor"] is True
    assert successor["gold_star_capabilities"]["exact_answer_authority"] is False
    assert successor["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert successor["user_reviewed_response"] is True
    assert successor["explicit_user_elevation_approval"] is True
    assert successor["elevation_approval_evidence"]
    assert successor["approval_state"].startswith("USER APPROVED GOLD STAR")
    assert successor["user_approved_at"] == "2026-11-26"
    assert successor["assistant_assessment_out_of_10"] == 9.5
    assert successor["transferable_lesson"]
    assert successor["transfer_boundary"]
    assert successor["freeze_policy"] == "immutable_user_approved_gold_standard"
    review_entry = next(item for item in review["entries"] if item["benchmark_id"] == SUCCESSOR_ID)
    assert review_entry["activation"] == "active_quality_contributor"
    assert SUCCESSOR_ID in {item["benchmark_id"] for item in transfer_map["entries"]}
    assert successor["numbering_unassigned_reason_code"] == "NO_SERIAL_ALLOCATION_REQUESTED"
    assert "NOT_EVALUATED" in successor["gold_star_capabilities"]["abstention_boundary"]
    assert successor["numbering_status"] == "UNASSIGNED"
    assert successor["doorway_status"] == "NOT_EVALUATED"

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
    assert "OBJECTIVE INTEGRITY:" in system_message
    assert "proxy" in system_message.casefold()
    assert "feedback loops" in system_message.casefold()
    assert "legitimate authority" in system_message.casefold()
    assert "a rising metric does not prove" in system_message.casefold()



def test_objective_integrity_instruction_is_not_added_to_unrelated_questions(monkeypatch):
    captured = {}

    def fake_route(**kwargs):
        captured.update(kwargs)
        return {"parsed": {"response": "Photosynthesis converts light energy into chemical energy."}}

    monkeypatch.setattr(composition, "route_with_model_bank", fake_route)
    monkeypatch.setattr(composition, "_gold_star_active_quality_contribution", lambda _query: None)
    composition._COMPOSITION_CACHE.clear()

    result = composition.compose(
        use_core=object(),
        query="What is photosynthesis?",
        context_data={},
    )

    assert result is not None
    system_message = next(
        item["content"] for item in captured["messages"] if item["role"] == "system"
    )
    assert "OBJECTIVE INTEGRITY:" not in system_message


def test_objective_integrity_instruction_requires_an_improvement_and_objective_signal():
    assert composition._objective_integrity_instruction(
        "How can we improve performance without compromising the mission objective?"
    )
    assert composition._objective_integrity_instruction(
        "How can we improve school test scores without narrowing learning?"
    )
    assert composition._objective_integrity_instruction(
        "Is this success metric still aligned with our goal?"
    )
    assert composition._objective_integrity_instruction(
        "How can I improve my running time?"
    ) == ""
    assert composition._objective_integrity_instruction(
        "What is photosynthesis?"
    ) == ""
