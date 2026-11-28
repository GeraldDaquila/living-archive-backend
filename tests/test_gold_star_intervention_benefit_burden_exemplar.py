import json
from pathlib import Path


def test_intervention_benefit_burden_power_consent_gold_star_is_frozen_standalone_exemplar():
    root = Path(__file__).resolve().parents[1]
    registry = json.loads((root / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    fixture = json.loads((root / "tests/fixtures/general-guide-intervention-benefit-burden-power-consent-accountability-2026-11-28.json").read_text(encoding="utf-8"))
    record = next(item for item in registry["records"] if item["benchmark_id"] == fixture["benchmark_id"])
    capabilities = record["gold_star_capabilities"]

    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == fixture["query"]
    assert record["expected_response"] == fixture["expected_response"]
    assert record["expected_doorway"] is None
    assert record["doorway_status"] == "NOT_EVALUATED"
    assert "NOT_EVALUATED" in capabilities["abstention_boundary"]
    assert record["runtime_transfer"] is False
    assert capabilities["generation_class"] == "user_approved_response_quality_exemplar"
    assert capabilities["standalone_response_quality_exemplar"] is True
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["active_quality_contributor"] is False
    assert capabilities["deterministic_fallback_eligible"] is False
    assert record["question_family_review"]["family_id"] == "qf-3696c7c39e394831"
    assert record["question_family_review"]["classification"] == "NEW_QUESTION_FAMILY"
    assert record["numbering_status"] == "UNASSIGNED"
