#!/usr/bin/env python3
"""Run seven held-out Gold Star cases with authored simulation fixtures only.

This is an offline harness exercise. It makes no HTTP/provider calls and must never
be interpreted as live visitor capture, attributable LLM evidence, or certification.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.guide_live_evaluation import build_human_review_template, evaluate_held

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUITE = ROOT / "docs/qa/guide_learning_evaluation_set.json"
SIMULATED_RESPONSES = {
    "heldout-water-boiling-point-001": (
        "At standard atmospheric pressure, water boils at 100°C (212°F). "
        "The boiling point changes when atmospheric pressure changes."
    ),
    "heldout-cosmology-life-001": (
        "Cosmology is the study of the universe as a whole. A picture of reality "
        "can shape people's values, choices, and relationships. For example, "
        "a community's understanding of its place in the world can influence "
        "how it treats the natural environment."
    ),
    "heldout-practical-trust-001": (
        "Ask the people affected what they see before deciding. Explain the reasons "
        "for the decision, name who is responsible, and follow through on promises. "
        "Then check with the people affected about the result."
    ),
    "heldout-strategic-governance-001": (
        "Centralized authority can provide coordination and oversight, while "
        "distributed authority delegates local decisions to teams. However, both "
        "models have costs and risks. When decisions carry organization-wide risk, "
        "consistent direction may help; routine local decisions can be delegated. "
        "I recommend a hybrid: retain strategic safeguards centrally and delegate "
        "bounded operational authority."
    ),
    "heldout-technical-verification-001": (
        "Use os.getenv('TOKEN') is not None as a boolean presence check. Do not "
        "print or log the secret value. This confirms that configuration is present, "
        "not that the application actually reads or uses the variable at runtime."
    ),
    "heldout-uncertain-causation-001": (
        "I cannot determine the cause without analytics and referral data. Compare "
        "referral sources, UTM campaign tags, Search Console, and server logs. "
        "Segment the traffic by landing page and inspect whether the increase came "
        "from search, a campaign, referrals, or bots."
    ),
    "heldout-explicit-no-handoff-001": (
        "A policy establishes the rule or principle that guides a decision. "
        "A procedure describes the steps for carrying it out. For example, a "
        "policy may require secure handling of records, while a procedure explains "
        "how staff store and access them."
    ),
}


def build_report(suite: dict) -> dict:
    cases = suite.get("cases")
    if not isinstance(cases, list) or len(cases) != 7:
        raise ValueError("The simulation requires exactly seven held-out cases.")
    rubric = suite["human_review_rubric"]
    results = []
    seen = set()
    for case in cases:
        case_id = case["case_id"]
        if case_id in seen:
            raise ValueError(f"Duplicate held-out case: {case_id}")
        seen.add(case_id)
        answer = SIMULATED_RESPONSES.get(case_id)
        if not answer:
            raise ValueError(f"No simulation response registered for {case_id}")
        checks = evaluate_held(
            {"case_id": case_id, "query": case["query"]},
            {"status": 200, "error": None, "body": {
                "ok": True,
                "response": answer,
                "recommendation": None,
                "response_provenance": {
                    "class": "simulated_fixture",
                    "provider": None,
                    "model": None,
                    "llm_invoked": False,
                },
            }},
        )
        results.append({
            "case_id": case_id,
            "question_type": case.get("question_type"),
            "query": case["query"],
            "simulated_candidate_response": answer,
            "provenance": {
                "class": "simulated_fixture",
                "provider": None,
                "model": None,
                "llm_invoked": False,
                "not_live_capture": True,
            },
            "heuristic_checks": checks,
            "heuristic_checks_passed": sum(item["passed"] for item in checks),
            "heuristic_checks_total": len(checks),
            "human_review": build_human_review_template(
                rubric, applicable_critical=case.get("critical_dimensions")
            ),
        })
    failed = [
        {"case_id": row["case_id"], "failed_checks": [
            item["name"] for item in row["heuristic_checks"] if not item["passed"]
        ]}
        for row in results if not all(item["passed"] for item in row["heuristic_checks"])
    ]
    return {
        "schema_version": "1.0",
        "report_type": "offline_simulation_only",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "simulation_only": True,
        "semantic_certification": False,
        "live_visitor_requests": 0,
        "provider_calls": 0,
        "attributable_llm_captures": 0,
        "paired_live_cases": 0,
        "human_calibration": "pending",
        "case_count": len(results),
        "cases_passing_all_heuristics": len(results) - len(failed),
        "cases_with_heuristic_failures": failed,
        "results": results,
        "interpretation": (
            "All responses are authored simulation fixtures. Passing heuristic checks "
            "validates the evaluator path only; it does not establish live service behavior, "
            "provider attribution, factual certification, independent human calibration, "
            "or browser acceptance. Human scorecards intentionally remain pending."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--output", type=Path, default=Path("artifacts/gold-star-wp3-simulation.json"))
    args = parser.parse_args()
    report = build_report(json.loads(args.suite.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "report_type": report["report_type"],
        "case_count": report["case_count"],
        "cases_passing_all_heuristics": report["cases_passing_all_heuristics"],
        "attributable_llm_captures": report["attributable_llm_captures"],
        "semantic_certification": report["semantic_certification"],
    }, indent=2))
    return 0 if not report["cases_with_heuristic_failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
