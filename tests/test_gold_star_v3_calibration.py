"""Gold Star v3 calibration against the current user-approved visitor question.

This is a GitHub Actions-only offline test. It uses the approved registry response,
does not call a provider or production service, and does not certify semantics.
"""
import json
from pathlib import Path

from gold_star_response_floor import (
    apply_response_floor_boundary,
    evaluate_response_floor,
)
from gold_star_semantic_contract import evaluate_semantic_contract

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ID = "gs-2026-11-21-organizational-acknowledgment-without-learning"


def _record():
    registry = json.loads(
        (ROOT / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8")
    )
    return next(item for item in registry["records"] if item["benchmark_id"] == BENCHMARK_ID)


def _payload(record, answer=None):
    doorway = record["expected_doorway"]
    return {
        "ok": True,
        "response": answer if answer is not None else record["expected_response"],
        "recommendation": {
            "title": doorway["title"],
            "url": doorway["url"],
        },
    }


def test_v3_calibration_approved_answer_passes_bounded_semantics_and_visitor_floor():
    record = _record()
    query = record["query"]
    payload = _payload(record)
    original_answer = payload["response"]
    original_doorway = dict(payload["recommendation"])

    semantic = evaluate_semantic_contract(query, payload)
    assert semantic["question_type"] == "institutional_learning_failure"
    assert semantic["status"] == "review_required"
    assert semantic["hard_failures"] == []
    assert all(check["passed"] for check in semantic["checks"])

    floor = evaluate_response_floor(query, payload)
    assert floor["status"] == "pass"
    assert floor["semantic_shadow"]["mode"] == "shadow_only"
    assert floor["semantic_shadow"]["semantic_certification"] is False
    assert floor["semantic_enforcement"]["mode"] == "bounded_supported_contract"
    assert floor["semantic_enforcement"]["enforced"] is True
    assert floor["semantic_enforcement"]["status"] == "pass"

    visitor_payload, status_code = apply_response_floor_boundary(query, payload, 200)
    assert status_code == 200
    assert visitor_payload["response"] == original_answer
    assert visitor_payload["recommendation"] == original_doorway
    assert visitor_payload["gold_star_v2_quality_floor"]["semantic_enforcement"]["status"] == "pass"


def test_v3_calibration_rejects_a_shallow_answer_at_the_supported_boundary():
    record = _record()
    weak = _payload(record, "Organizations repeat failures because people forget.")
    semantic = evaluate_semantic_contract(record["query"], weak)
    assert semantic["status"] == "fail"
    assert semantic["hard_failures"]

    floor = evaluate_response_floor(record["query"], weak)
    assert floor["status"] == "fail"
    assert floor["reason"] == "supported_semantic_contract_failed"
    assert floor["semantic_enforcement"]["enforced"] is True
    assert floor["semantic_enforcement"]["status"] == "fail"


def test_v3_calibration_does_not_overgeneralize_to_adjacent_organization_questions():
    query = "Why do teams sometimes resist organizational change?"
    payload = {"ok": True, "response": "Teams may resist change when costs, uncertainty, or lost influence are not addressed."}
    floor = evaluate_response_floor(query, payload)
    assert floor["status"] == "pass"
    assert floor["semantic_enforcement"]["enforced"] is False
    assert floor["semantic_enforcement"]["reason"] == "no_enforced_supported_question_type"
