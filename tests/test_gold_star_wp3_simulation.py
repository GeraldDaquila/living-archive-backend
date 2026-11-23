import json
from pathlib import Path

import pytest

from scripts.gold_star_wp3_simulation import build_report

ROOT = Path(__file__).resolve().parents[1]


def _suite():
    return json.loads((ROOT / "docs/qa/guide_learning_evaluation_set.json").read_text())


def test_eight_simulated_responses_exercise_every_heldout_rubric_without_claiming_live_evidence():
    report = build_report(_suite())
    assert report["report_type"] == "offline_simulation_only"
    assert report["simulation_only"] is True
    assert report["case_count"] == 8
    assert report["cases_passing_all_heuristics"] == 8
    assert report["cases_with_heuristic_failures"] == []
    assert report["live_visitor_requests"] == 0
    assert report["provider_calls"] == 0
    assert report["attributable_llm_captures"] == 0
    assert report["paired_live_cases"] == 0
    assert report["semantic_certification"] is False
    for case in report["results"]:
        assert case["provenance"]["class"] == "simulated_fixture"
        assert case["provenance"]["not_live_capture"] is True
        assert case["human_review"]["status"] == "PENDING"
        assert all(item["passed"] for item in case["heuristic_checks"])


def test_simulation_fails_closed_when_a_heldout_case_has_no_response():
    from scripts import gold_star_wp3_simulation as simulation
    original = simulation.SIMULATED_RESPONSES.pop("heldout-explicit-no-handoff-001")
    try:
        with pytest.raises(ValueError, match="No simulation response"):
            build_report(_suite())
    finally:
        simulation.SIMULATED_RESPONSES["heldout-explicit-no-handoff-001"] = original


def test_simulation_rejects_duplicate_or_incomplete_case_sets():
    suite = _suite()
    suite["cases"][-1] = dict(suite["cases"][0])
    with pytest.raises(ValueError, match="Duplicate held-out case"):
        build_report(suite)
    suite = _suite()
    suite["cases"] = suite["cases"][:-1]
    with pytest.raises(ValueError, match="exactly eight"):
        build_report(suite)
