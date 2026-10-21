"""Offline replay of simulated fallback cohorts; never changes live decisions."""
import json
from pathlib import Path

import main
from guide_fuzzy_relevance import score_resource_fit

FIXTURE = Path(__file__).parent / "fixtures" / "fuzzy_fallback_replay_simulated_cases.json"
FALLBACK_METRIC_PATHWAYS = {"provider_bank_exhausted", "composition_exception"}


def _classify(baseline_correct, shadow_correct, tied, candidate_set_sufficient):
    if not candidate_set_sufficient:
        return "insufficient_candidate_set"
    if tied:
        return "tie_or_ambiguous"
    if baseline_correct and shadow_correct:
        return "correct_unchanged_baseline"
    if not baseline_correct and shadow_correct:
        return "potential_recovery"
    if baseline_correct and not shadow_correct:
        return "potential_regression"
    return "both_miss_simulated_expectation"


def test_simulated_fallback_replay_reports_pathways_and_counterfactuals():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert fixture["status"] == "SIMULATED_DIAGNOSTIC_ONLY"
    assert fixture["production_data_present"] is False
    assert fixture["independent_human_review"] == "pending"
    assert all(case["case_origin"] == "simulated" for case in fixture["cases"])

    outcomes = []
    for case in fixture["cases"]:
        candidates = [dict(candidate) for candidate in case["candidates"]]
        before = [dict(candidate) for candidate in candidates]
        baseline = main._canonical_primary_from_docs(
            candidates, case["query"], {"action": "recommendation"}
        )
        baseline_id = next(
            (candidate["candidate_id"] for candidate in candidates
             if baseline is not None and candidate["title"] == baseline.get("title")),
            None,
        )
        scored = [
            (candidate["candidate_id"],
             score_resource_fit(case["query"], candidate)["overall_shadow_score"])
            for candidate in candidates
        ]
        shadow_id, shadow_score = max(scored, key=lambda pair: pair[1])
        tied = sum(score == shadow_score for _, score in scored) > 1
        expected_id = case["expected_relevant_candidate_id"]
        baseline_correct = baseline_id == expected_id
        shadow_correct = not tied and shadow_id == expected_id
        outcome = {
            "case_id": case["case_id"],
            "pathway": case["pathway"],
            "baseline_selected": baseline_id,
            "shadow_counterfactual": None if tied else shadow_id,
            "shadow_tie": tied,
            "expected_relevant_candidate_id": expected_id,
            "baseline_matches_simulated_expectation": baseline_correct,
            "shadow_matches_simulated_expectation": shadow_correct,
            "diagnostic_classification": _classify(
                baseline_correct, shadow_correct, tied, case["candidate_set_sufficient"]
            ),
            "eligible_for_fallback_cohort_summary": case["pathway"] in FALLBACK_METRIC_PATHWAYS,
            "candidate_set_sufficient_author_assumption": case["candidate_set_sufficient"],
        }
        outcomes.append(outcome)
        assert candidates == before, "scoring or selector must not mutate candidate records"

    classifications = {}
    for item in outcomes:
        key = item["diagnostic_classification"]
        classifications[key] = classifications.get(key, 0) + 1
    print(f"SIMULATED FALLBACK REPLAY CLASSIFICATIONS: {classifications}")

    for pathway in sorted({case["pathway"] for case in fixture["cases"]}):
        cohort = [item for item in outcomes if item["pathway"] == pathway]
        print(
            "SIMULATED FALLBACK REPLAY COHORT: "
            f"pathway={pathway}; cases={len(cohort)}; "
            f"baseline_expected={sum(x['baseline_matches_simulated_expectation'] for x in cohort)}/"
            f"{len(cohort)}; shadow_expected={sum(x['shadow_matches_simulated_expectation'] for x in cohort)}/"
            f"{len(cohort)}; ties={sum(x['shadow_tie'] for x in cohort)}"
        )
    print(f"SIMULATED FALLBACK REPLAY CASES: {outcomes}")

    assert {case["pathway"] for case in fixture["cases"]} >= {
        "provider_bank_exhausted", "composition_exception", "individual_provider_failure"
    }
    assert all(item["eligible_for_fallback_cohort_summary"] is False
               for item in outcomes if item["pathway"] == "individual_provider_failure")
    assert all(item["eligible_for_fallback_cohort_summary"] is True
               for item in outcomes if item["pathway"] in FALLBACK_METRIC_PATHWAYS)

    # Keep the known consultation miss visible; this guards observability, not
    # a requirement that future scorer versions continue to fail this case.
    consultation = next(
        item for item in outcomes if item["case_id"] == "sim-exhaustion-consultation"
    )
    assert consultation["diagnostic_classification"] == "tie_or_ambiguous"
    assert consultation["baseline_selected"] is None
    assert consultation["shadow_counterfactual"] is None
    insufficient = next(
        item for item in outcomes if item["case_id"] == "sim-exhaustion-no-sufficient-candidate"
    )
    assert insufficient["diagnostic_classification"] == "insufficient_candidate_set"
    assert insufficient["candidate_set_sufficient_author_assumption"] is False
    # Do not assert either selector returns no candidate here: record the observed
    # behavior as a potential false-positive signal if either recommends one.
    print(
        "INSUFFICIENT-CANDIDATE SAFETY AUDIT: "
        f"case={insufficient['case_id']}; baseline_selected={insufficient['baseline_selected']}; "
        f"shadow_counterfactual={insufficient['shadow_counterfactual']}; "
        "review_required=True"
    )
    # Expectations are author-authored simulations, not independent ground truth.
