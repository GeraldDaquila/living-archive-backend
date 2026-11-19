"""Governance tests for the delegated WP3 deterministic review dossier."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "docs/qa/gold_star_wp3_deterministic_review_2026-11-19.json"
CAPTURE = ROOT / "docs/qa/gold_star_wp3_paired_capture_2026-11-19.json"
EXPECTED = {
    "heldout-water-boiling-point-001",
    "heldout-cosmology-life-001",
    "heldout-practical-trust-001",
    "heldout-strategic-governance-001",
    "heldout-technical-verification-001",
    "heldout-uncertain-causation-001",
    "heldout-explicit-no-handoff-001",
}
VALID = {0, 1, 2, "NA"}


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_delegated_review_covers_all_seven_frozen_cases_without_claiming_independent_human_review():
    dossier = _load(DOSSIER)
    ids = [case["case_id"] for case in dossier["cases"]]
    assert len(ids) == len(set(ids)) == 7
    assert set(ids) == EXPECTED
    assert dossier["review_mode"] == "delegated_evidence_based_technical_stewardship_review"
    assert dossier["scoring"]["independent_human_review"] is False
    assert dossier["scoring"]["semantic_certification"] is False
    assert dossier["registry"]["user_approved_gold_standards"] == 114
    assert dossier["registry"]["total_records"] == 152


def test_each_case_has_complete_dimension_scores_and_explicit_case_critical_scores():
    dossier = _load(DOSSIER)
    required = set(dossier["scoring"]["dimensions"])
    for case in dossier["cases"]:
        assert case["status"] == "DELEGATED_REVIEW_COMPLETE"
        assert case["decision"] == "REVISE"
        assert set(case["scores"]) == required
        assert set(case["case_specific_scores"]) == set(case["critical_dimensions"])
        assert all(value in VALID for value in case["scores"].values())
        assert all(value in VALID - {"NA"} for value in case["case_specific_scores"].values())
        assert case["reviewer_notes"].strip()
        assert case["reviewed_at"] == "2026-11-19"


def test_capture_report_retains_original_outputs_and_attaches_review_without_claiming_llm_parity():
    dossier = _load(DOSSIER)
    capture = _load(CAPTURE)
    assert capture["paired_summary"]["deterministic_captured"] == 7
    assert capture["paired_summary"]["llm_captured"] == 0
    assert capture["paired_summary"]["paired_cases"] == 0
    assert capture["semantic_certification"] is False
    assert capture["human_review_summary"]["independent_human_review"] is False
    assert dossier["registry"]["content_sha"] == capture["human_review_summary"]["registry_content_sha"]
    assert len(dossier["registry"]["content_sha"]) == 40
    assert {case["case_id"] for case in capture["cases"]} == EXPECTED
    for case in capture["cases"]:
        review = next(item for item in dossier["cases"] if item["case_id"] == case["case_id"])
        assert case["deterministic"]["response"] == case["deterministic"]["capture"]["visitor_sanitized_response"]
        assert case["human_review"]["deterministic"]["decision"] == review["decision"]
        assert case["human_review"]["deterministic"]["case_specific_scores"] == review["case_specific_scores"]
        assert case["llm"] is None

def test_every_review_includes_a_task_specific_correction_without_creating_new_gold_stars():
    dossier = _load(DOSSIER)
    for case in dossier["cases"]:
        assert case["corrective_direction"].strip()
        assert case["corrective_direction_is_new_gold_star_text"] is False
        assert isinstance(case["supporting_benchmarks"], list)
    technical = next(
        case for case in dossier["cases"]
        if case["case_id"] == "heldout-technical-verification-001"
    )
    assert technical["supporting_benchmarks"] == []
    assert "general Python guidance" in technical["corrective_direction"]
    no_handoff = next(
        case for case in dossier["cases"]
        if case["case_id"] == "heldout-explicit-no-handoff-001"
    )
    assert no_handoff["supporting_benchmarks"] == []
    assert "follow-up question" in no_handoff["corrective_direction"]
