"""Simulated question battery for broad fuzzy-relevance diagnostic evaluation."""
import json
from pathlib import Path

from guide_fuzzy_relevance import score_resource_fit

FIXTURE = Path(__file__).parent / "fixtures" / "guide_fuzzy_relevance_simulated_question_battery.json"


def _cases():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]


def test_simulated_question_battery_has_ten_distinct_labeled_cases():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    cases = fixture["cases"]
    assert fixture["status"] == "ADDITIVE_SIMULATED_EVALUATION"
    assert fixture["frozen_benchmark_modified"] is False
    assert len(cases) == 10
    assert len({case["id"] for case in cases}) == len(cases)
    assert all(case["direct"]["title"] != case["distractor"]["title"] for case in cases)


def test_simulated_question_battery_reports_pairwise_accuracy_and_failures():
    """Keep this a diagnostic report: expose weaknesses rather than tune labels to pass."""
    outcomes = []
    for case in _cases():
        direct = score_resource_fit(case["query"], case["direct"])["overall_shadow_score"]
        distractor = score_resource_fit(case["query"], case["distractor"])["overall_shadow_score"]
        outcomes.append({
            "case": case["id"],
            "direct": direct,
            "distractor": distractor,
            "correct": direct > distractor,
            "tie": direct == distractor,
        })

    correct = sum(item["correct"] for item in outcomes)
    ties = sum(item["tie"] for item in outcomes)
    accuracy = correct / len(outcomes)
    failures = [item for item in outcomes if not item["correct"]]
    print(f"SIMULATED FUZZY EVALUATION: {correct}/{len(outcomes)} correct ({accuracy:.0%}); ties={ties}; failures={failures}")
    print(f"SIMULATED FUZZY SCORES: {outcomes}")
    for item in failures:
        case = next(case for case in _cases() if case["id"] == item["case"])
        print("FAILED CASE DIMENSIONS", item["case"], score_resource_fit(case["query"], case["direct"]), score_resource_fit(case["query"], case["distractor"]))
    # Broad diagnostic threshold, not a claim of production readiness.
    assert accuracy >= 0.70, (
        f"Simulated pairwise accuracy {correct}/{len(outcomes)} ({accuracy:.0%}); "
        f"ties={ties}; failures={failures}; all_scores={outcomes}"
    )


def test_simulated_question_battery_scores_are_bounded_and_candidates_unchanged():
    for case in _cases():
        for key in ("direct", "distractor"):
            candidate = dict(case[key])
            before = dict(candidate)
            score = score_resource_fit(case["query"], candidate)["overall_shadow_score"]
            assert 0.0 <= score <= 1.0
            assert candidate == before
