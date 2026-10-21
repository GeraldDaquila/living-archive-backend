"""Second simulated challenge set to probe generalization beyond tuned examples."""
import json
from pathlib import Path

from guide_fuzzy_relevance import score_resource_fit

FIXTURE = Path(__file__).parent / "fixtures" / "guide_fuzzy_relevance_independent_challenge_set.json"


def _cases():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]


def test_independent_challenge_fixture_is_additive_and_distinct():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    cases = fixture["cases"]
    assert fixture["status"] == "ADDITIVE_CHALLENGE_EVALUATION"
    assert fixture["frozen_benchmark_modified"] is False
    assert len(cases) == 8
    assert len({case["id"] for case in cases}) == len(cases)
    assert all(case["direct"]["title"] != case["distractor"]["title"] for case in cases)


def test_independent_challenge_pairwise_accuracy_floor():
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
    print(f"INDEPENDENT CHALLENGE: {correct}/{len(outcomes)} correct ({accuracy:.0%}); ties={ties}; failures={failures}")
    print(f"INDEPENDENT CHALLENGE SCORES: {outcomes}")
    assert accuracy >= 0.70, (
        f"Independent challenge accuracy {correct}/{len(outcomes)} ({accuracy:.0%}); "
        f"ties={ties}; failures={failures}; scores={outcomes}"
    )


def test_independent_challenge_scores_bounded_and_candidates_unchanged():
    for case in _cases():
        for key in ("direct", "distractor"):
            candidate = dict(case[key])
            before = dict(candidate)
            score = score_resource_fit(case["query"], candidate)["overall_shadow_score"]
            assert 0.0 <= score <= 1.0
            assert candidate == before
