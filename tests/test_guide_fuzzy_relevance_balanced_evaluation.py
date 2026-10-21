"""Balanced evaluation of fuzzy relevance shadow scores.

This evaluates ordering only. It does not alter production ranking or resource selection.
"""
import json
from pathlib import Path

from guide_fuzzy_relevance import score_resource_fit


FIXTURE = Path(__file__).parent / "fixtures" / "guide_fuzzy_relevance_balanced_evaluation.json"


def _load_cases():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]


def test_balanced_cases_rank_direct_resources_above_unsuitable_resources():
    failures = []
    for case in _load_cases():
        direct = score_resource_fit(case["query"], case["direct"])["overall_shadow_score"]
        unsuitable = score_resource_fit(case["query"], case["unsuitable"])["overall_shadow_score"]
        if direct <= unsuitable:
            failures.append((case["id"], direct, unsuitable))
    assert not failures, f"Direct-vs-unsuitable ranking failures: {failures}"


def test_balanced_cases_rank_direct_resources_above_adjacent_resources():
    failures = []
    for case in _load_cases():
        direct = score_resource_fit(case["query"], case["direct"])["overall_shadow_score"]
        adjacent = score_resource_fit(case["query"], case["adjacent"])["overall_shadow_score"]
        if direct <= adjacent:
            failures.append((case["id"], direct, adjacent))
    assert not failures, f"Direct-vs-adjacent ranking failures: {failures}"


def test_scores_remain_diagnostic_and_do_not_mutate_evaluation_candidates():
    for case in _load_cases():
        candidates = [case["direct"], case["adjacent"], case["unsuitable"]]
        snapshots = [dict(candidate) for candidate in candidates]
        scores = [score_resource_fit(case["query"], candidate) for candidate in candidates]
        assert candidates == snapshots
        assert all(0.0 <= score["overall_shadow_score"] <= 1.0 for score in scores)


def test_fixture_is_additive_and_does_not_replace_frozen_benchmark():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert fixture["status"] == "ADDITIVE_EVALUATION_FIXTURE"
    assert fixture["frozen_benchmark_modified"] is False
    assert len(fixture["cases"]) >= 4
    assert {case["id"] for case in fixture["cases"]} >= {
        "ethical-tradeoff", "harm-repair", "collective-next-step", "accountability"
    }
