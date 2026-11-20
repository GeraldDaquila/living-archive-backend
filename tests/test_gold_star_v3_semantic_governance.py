"""Gold Star v3 explicit semantic operating-state reporting.

These assertions verify reporting only; the v2 visitor decision is unchanged.
"""
import json
from pathlib import Path

from gold_star_response_floor import evaluate_response_floor


def _approved_payload():
    root = Path(__file__).resolve().parents[1]
    registry = json.loads((root / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    record = next(item for item in registry["records"] if item["benchmark_id"] == "gs-2026-11-21-organizational-acknowledgment-without-learning")
    doorway = record["expected_doorway"]
    return record["query"], {
        "ok": True,
        "response": record["expected_response"],
        "recommendation": {"title": doorway["title"], "url": doorway["url"]},
    }


def test_supported_family_reports_observation_bounded_enforcement_and_no_certification():
    query, payload = _approved_payload()
    result = evaluate_response_floor(query, payload)
    states = result["semantic_governance"]

    assert result["status"] == "pass"
    assert states["diagnostic_observation"]["state"] == "available"
    assert states["diagnostic_observation"]["mode"] == "shadow_only"
    assert states["bounded_enforcement"]["state"] == "active"
    assert states["bounded_enforcement"]["status"] == "pass"
    assert states["semantic_certification"] == {
        "state": "not_certified",
        "certified": False,
        "reason": "heuristic_contracts_and_offline_calibration_do_not_establish_semantic_certification",
    }


def test_adjacent_question_reports_diagnostic_only_without_bounded_enforcement():
    query = "Why do teams sometimes resist organizational change?"
    result = evaluate_response_floor(
        query,
        {"ok": True, "response": "Teams may resist change when uncertainty and perceived costs are not addressed."},
    )
    states = result["semantic_governance"]

    assert result["status"] == "pass"
    assert states["diagnostic_observation"]["state"] == "available"
    assert states["bounded_enforcement"]["state"] == "inactive"
    assert states["bounded_enforcement"]["status"] == "not_applicable"
    assert states["semantic_certification"]["certified"] is False


def test_semantic_failure_is_reported_without_claiming_certification():
    query = "Why do organizations repeat failures they publicly acknowledge?"
    result = evaluate_response_floor(query, {"ok": True, "response": "Organizations repeat failures because people forget."})
    states = result["semantic_governance"]

    assert result["status"] == "fail"
    assert states["bounded_enforcement"]["state"] == "active"
    assert states["bounded_enforcement"]["status"] == "fail"
    assert states["semantic_certification"]["state"] == "not_certified"
    assert states["semantic_certification"]["certified"] is False
