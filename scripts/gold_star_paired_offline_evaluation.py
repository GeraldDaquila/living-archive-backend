#!/usr/bin/env python3
"""Offline paired-path Gold Star contract evaluation; no provider or network calls."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from gold_star_semantic_contract import evaluate_semantic_contract

PATHS = ("llm", "deterministic")

def evaluate_dataset(dataset: dict) -> dict:
    cases = dataset.get("cases")
    if not isinstance(cases, list):
        raise ValueError("dataset.cases must be a list")
    results = []
    for case in cases:
        if not isinstance(case, dict) or not case.get("case_id") or not case.get("query"):
            raise ValueError("each case requires case_id and query")
        row = {"case_id": case["case_id"], "question_type": case.get("question_type"), "paths": {}}
        for path in PATHS:
            payload = case.get(path)
            if payload is None:
                row["paths"][path] = {"status": "not_applicable", "reason": "no_supported_fixture"}
            else:
                row["paths"][path] = evaluate_semantic_contract(case["query"], payload)
        row["parity"] = (
            row["paths"]["llm"].get("status") == row["paths"]["deterministic"].get("status")
            if all(row["paths"][p].get("status") != "not_applicable" for p in PATHS)
            else None
        )
        results.append(row)
    summary = {}
    for path in PATHS:
        applicable = [r["paths"][path] for r in results if r["paths"][path].get("status") != "not_applicable"]
        summary[path] = {
            "applicable": len(applicable),
            "not_applicable": len(results) - len(applicable),
            "contract_violations": sum(x.get("status") == "fail" for x in applicable),
            "review_required": sum(x.get("status") == "review_required" for x in applicable),
            "heuristic_passes_are_not_certifications": True,
        }
    paired = [r for r in results if r["parity"] is not None]
    return {
        "schema_version": "1.0",
        "evaluation_mode": "offline_fixture_only",
        "semantic_certification": False,
        "paired_cases": len(paired),
        "status_parity": sum(r["parity"] is True for r in paired),
        "status_disagreement": sum(r["parity"] is False for r in paired),
        "coverage": summary,
        "results": results,
        "interpretation": "This harness checks observable task-contract failures on supplied fixtures. It does not generate answers, verify factual truth, or replace blinded human review.",
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/gold-star-paired-offline-report.json"))
    args = parser.parse_args()
    report = evaluate_dataset(json.loads(args.dataset.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("paired_cases", "status_parity", "status_disagreement", "coverage")}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
