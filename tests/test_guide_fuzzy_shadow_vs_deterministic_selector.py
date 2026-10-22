"""Paired comparison of unchanged deterministic selection and fuzzy shadow diagnostics."""
import json
from pathlib import Path

import main
from guide_fuzzy_relevance import score_resource_fit

FIXTURE = Path(__file__).parent / "fixtures" / "guide_fuzzy_relevance_independent_challenge_set.json"


def test_paired_deterministic_selector_vs_shadow_score_report():
    """Report agreement on identical candidates; do not let shadow scores select."""
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
    outcomes = []
    for case in cases:
        candidates = []
        for key in ("direct", "distractor"):
            candidate = dict(case[key])
            candidate["url"] = (
                "https://geralddaquila.com/evaluation/" + case["id"] + "/" + key + "/"
            )
            candidates.append(candidate)

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

    assert total == len(cases)
    assert all(item["deterministic_choice"] in {"direct", "distractor", "none"} for item in outcomes)
