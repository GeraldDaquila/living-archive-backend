import json
from pathlib import Path

import gold_star_lessons
from scripts.capture_gold_star_matched_pairs import _load_cases


ROOT = Path(__file__).resolve().parents[1]
CASE_SET = ROOT / "docs" / "qa" / "objective_integrity_matched_pair_cases.json"
TARGET_ID = "general-guide-developmental-stewardship-objective-integrity-2026-11-26"


def test_objective_integrity_pilot_is_preregistered_across_three_heldout_families():
    suite, cases, target = _load_cases(CASE_SET)
    assert suite["evaluation_id"] == "gold-star-objective-integrity-heldout-pilot-2026-11-26"
    assert target == TARGET_ID
    assert len(cases) == 6
    assert len({case["case_family"] for case in cases}) == 3
    assert all(case["case_id"].startswith("heldout-objective-integrity-") for case in cases)
    assert "community garden" not in " ".join(case["query"].lower() for case in cases)
    assert "school" not in " ".join(case["query"].lower() for case in cases)


def test_target_gold_star_is_retrieved_for_every_heldout_objective_integrity_case():
    suite, cases, target = _load_cases(CASE_SET)
    for case in cases:
        candidates = gold_star_lessons.select_lesson_candidates(case["query"], limit=4)
        assert target in {item["benchmark_id"] for item in candidates}, case["case_id"]


def test_objective_integrity_gold_star_is_excluded_from_unrelated_negative_control():
    suite, _, target = _load_cases(CASE_SET)
    candidates = gold_star_lessons.select_lesson_candidates(
        suite["negative_control_query"], limit=4
    )
    assert target not in {item["benchmark_id"] for item in candidates}


def test_each_case_has_a_case_specific_rubric_and_primary_transfer_dimension():
    _, cases, _ = _load_cases(CASE_SET)
    for case in cases:
        assert len(case["rubric"]) >= 4
        assert "objective_integrity_reasoning" in case["critical_dimensions"]
        assert len(set(case["critical_dimensions"])) == len(case["critical_dimensions"])
