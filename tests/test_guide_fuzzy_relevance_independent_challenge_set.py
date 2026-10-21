"""Independent challenge evaluation for fuzzy relevance shadow scoring.

The cases are simulated diagnostic probes, not human-validated semantic ground
truth. Pairwise ties and losses remain explicit in the report.
"""
import json
from pathlib import Path

from guide_fuzzy_relevance import score_resource_fit

FIXTURE = Path(__file__).parent / "fixtures" / "guide_fuzzy_relevance_independent_challenge_set.json"
CONCEPT_DIMENSIONS = (
    "ethical_tradeoff",
    "harm_repair",
    "accountability",
    "governance",
    "collective_next_step",
    "belonging_identity",
    "power_fairness",
)


def _cases():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]


def _score_case(case):
    direct = score_resource_fit(case["query"], case["direct"])
    distractor = score_resource_fit(case["query"], case["distractor"])
    direct_score = direct["overall_shadow_score"]
    distractor_score = distractor["overall_shadow_score"]
    return {
        "case": case["id"],
        "direct": direct_score,
        "distractor": distractor_score,
        "margin": round(direct_score - distractor_score, 4),
        "correct": direct_score > distractor_score,
        "tie": direct_score == distractor_score,
        "direct_dimensions": direct,
        "distractor_dimensions": distractor,
    }


def test_independent_challenge_fixture_is_additive_and_distinct():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    cases = fixture["cases"]
    assert fixture["status"] == "ADDITIVE_CHALLENGE_EVALUATION"
    assert fixture["frozen_benchmark_modified"] is False
    assert len(cases) >= 12
    assert len({case["id"] for case in cases}) == len(cases)
    assert all(case["direct"]["title"] != case["distractor"]["title"] for case in cases)
    assert any("negative-control" in case["id"] for case in cases)


def test_independent_challenge_pairwise_accuracy_floor_and_diagnostic_report():
    outcomes = [_score_case(case) for case in _cases()]
    total = len(outcomes)
    wins = sum(item["correct"] for item in outcomes)
    ties = sum(item["tie"] for item in outcomes)
    losses = total - wins - ties
    accuracy = wins / total if total else 0.0
    failures = [item for item in outcomes if not item["correct"]]

    # Per-dimension aggregates help reveal whether a category is consistently
    # unobserved, rather than treating the aggregate score as a black box.
    dimension_summary = {}
    for dimension in (*CONCEPT_DIMENSIONS, "query_title_overlap", "query_body_overlap"):
        values = [
            item[side][dimension]
            for item in outcomes
            for side in ("direct_dimensions", "distractor_dimensions")
        ]
        dimension_summary[dimension] = {
            "nonzero_candidate_scores": sum(value > 0 for value in values),
            "candidate_scores": len(values),
            "mean_score": round(sum(values) / max(1, len(values)), 4),
        }

    print(
        "INDEPENDENT CHALLENGE SUMMARY: "
        f"wins={wins}/{total} ({accuracy:.1%}); ties={ties}; losses={losses}; "
        f"failures={[{'case': item['case'], 'direct': item['direct'], 'distractor': item['distractor'], 'margin': item['margin']} for item in failures]}"
    )
    print(f"INDEPENDENT CHALLENGE PER-DIMENSION SUMMARY: {dimension_summary}")
    print(f"INDEPENDENT CHALLENGE FULL SCORE VECTORS: {outcomes}")

    # This is an evaluation floor, not a production-readiness threshold. All
    # ties/failures are still printed and preserved as visible evidence.
    assert accuracy >= 0.60, (
        f"Independent challenge accuracy {wins}/{total} ({accuracy:.1%}); "
        f"ties={ties}; losses={losses}; failures={failures}"
    )


def test_neighborhood_nonconsultation_gap_is_explicitly_reported():
    cases = {case["id"]: case for case in _cases()}
    outcome = _score_case(cases["neighborhood-not-consulted"])
    # Preserve the known weakness as an observable diagnostic, not a corrected
    # label or a brittle assertion that a future scorer must keep failing.
    print(
        "KNOWN PARAPHRASE GAP neighborhood-not-consulted: "
        f"direct={outcome['direct']}; distractor={outcome['distractor']}; "
        f"margin={outcome['margin']}; "
        f"direct_dimensions={outcome['direct_dimensions']}; "
        f"distractor_dimensions={outcome['distractor_dimensions']}"
    )
    assert outcome["case"] == "neighborhood-not-consulted"
    assert outcome["direct"] >= 0.0
    assert outcome["distractor"] >= 0.0


def test_independent_challenge_scores_bounded_and_candidates_unchanged():
    for case in _cases():
        for key in ("direct", "distractor"):
            candidate = dict(case[key])
            before = dict(candidate)
            score = score_resource_fit(case["query"], candidate)
            assert all(0.0 <= value <= 1.0 for value in score.values())
            assert candidate == before



def test_paired_deterministic_selector_vs_shadow_score_report():
    """Compare the unchanged deterministic selector with shadow scores on identical pairs.

    This is a diagnostic comparison, not a claim that the fixture labels are
    independent ground truth. The scorer never participates in selection.
    """
    import main

    outcomes = []
    for case in _cases():
        candidates = []
        for key in ("direct", "distractor"):
            candidate = dict(case[key])
            candidate["url"] = (
                "https://geralddaquila.com/evaluation/"
                + case["id"] + "/" + key + "/"
            )
            candidates.append(candidate)

        # Invoke the existing deterministic selector independently of shadow scoring.
        baseline = main._canonical_primary_from_docs(
            candidates, case["query"], {"action": "recommendation"}
        )
        if baseline is None:
            baseline_choice = "none"
        elif baseline["title"] == candidates[0]["title"]:
            baseline_choice = "direct"
        elif baseline["title"] == candidates[1]["title"]:
            baseline_choice = "distractor"
        else:
            baseline_choice = "unexpected"

        direct_score = score_resource_fit(case["query"], candidates[0])["overall_shadow_score"]
        distractor_score = score_resource_fit(case["query"], candidates[1])["overall_shadow_score"]
        shadow_choice = (
            "direct" if direct_score > distractor_score
            else "distractor" if distractor_score > direct_score
            else "tie"
        )
        outcomes.append({
            "case": case["id"],
            "deterministic_choice": baseline_choice,
            "shadow_choice": shadow_choice,
            "deterministic_matches_shadow": baseline_choice == shadow_choice,
            "deterministic_selects_direct": baseline_choice == "direct",
            "shadow_selects_direct": shadow_choice == "direct",
        })

    total = len(outcomes)
    baseline_direct = sum(item["deterministic_selects_direct"] for item in outcomes)
    baseline_none = sum(item["deterministic_choice"] == "none" for item in outcomes)
    baseline_distractor = sum(item["deterministic_choice"] == "distractor" for item in outcomes)
    shadow_direct = sum(item["shadow_selects_direct"] for item in outcomes)
    agreement = sum(item["deterministic_matches_shadow"] for item in outcomes)

    print(
        "PAIRED DETERMINISTIC VS SHADOW: "
        f"cases={total}; deterministic_direct={baseline_direct}; "
        f"deterministic_distractor={baseline_distractor}; deterministic_none={baseline_none}; "
        f"shadow_direct={shadow_direct}; selector_shadow_agreement={agreement}/{total}"
    )
    print(f"PAIRED DETERMINISTIC VS SHADOW CASES: {outcomes}")

    assert total == len(_cases())
    assert all(item["deterministic_choice"] in {"direct", "distractor", "none"} for item in outcomes)
    # Structural safety: shadow values are not passed into or used to order the
    # deterministic selector's input candidates.
    assert all("_fuzzy_relevance_shadow" not in candidate for case in _cases() for candidate in (case["direct"], case["distractor"]))
