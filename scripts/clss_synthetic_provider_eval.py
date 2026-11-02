"""Synthetic-only CLSS provider evaluation runner.

Invoked only by the dedicated manual GitHub Actions workflow. It sends only
repository-owned synthetic fixtures to Groq and writes a review artifact.
No visitor answers, persistence service, telemetry, or production integration.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path

from clss_deterministic_response import build_deterministic_response
from clss_response_validator import validate_candidate_response

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/clss/stewardship-coherence-cases.json"
OUT = ROOT / "clss-evaluation-output"
API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = os.environ.get("CLSS_EVAL_MODEL", "openai/gpt-oss-120b")
API_KEY = os.environ.get("GROQ_API_KEY", "")

SYSTEM = """You are producing a cautious CLSS evidence synthesis candidate for human review.
Treat every supplied answer as an unverified account. Preserve source type exactly:
first_hand_observation, second_hand_report, documented_outcome, self_report,
interpretation, or unknown. Do not convert reports into established facts.
Do not infer private motives, diagnose, score, rank, or decide suitability.
Missing information is unknown, never adverse evidence. Preserve repair,
counterevidence, time pressure, and unresolved disagreement. Do not manufacture
a tension. Cite only evidence IDs supplied. Return one JSON object and no prose.
The object must have exactly these top-level fields:
mode, path, central_incoherence, why_it_matters, what_the_evidence_says,
what_could_change_the_interpretation, what_to_do_next, limits.
path must be "llm". central_incoherence has exactly text, finding_type,
evidence_ids. finding_type must be one of supported_tension, mixed_evidence,
insufficient_evidence, no_defensible_tension.
why_it_matters has exactly text and evidence_ids.
what_the_evidence_says and what_could_change_the_interpretation are arrays
of objects with exactly text and evidence_ids.
what_to_do_next has exactly action, owner (string or null), observable_indicators
(non-empty string array). limits is a string array. Every evidence statement
must cite its source ID. Do not invent evidence or claim verification."""

def call_model(case):
    evidence = case.get("evidence", [])
    # Deliberately blind the model to fixture expectations and reviewer criteria.
    # Those remain in the offline report for independent comparison.
    payload = {
        "case_id": case["id"],
        "mode": case["mode"],
        "evidence": evidence,
        "missing_dimensions": case.get("missing_dimensions", []),
        "instruction": "Reason independently from the supplied evidence. Do not assume a tension exists.",
    }
    request_body = {
        "model": MODEL,
        "temperature": 0,
        "max_tokens": 1800,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    started = time.monotonic()
    with urllib.request.urlopen(req, timeout=50) as response:
        result = json.loads(response.read().decode("utf-8"))
    elapsed_ms = round((time.monotonic() - started) * 1000)
    content = result["choices"][0]["message"]["content"]
    usage = result.get("usage", {})
    return content, elapsed_ms, usage

def main():
    if not API_KEY:
        raise SystemExit("GROQ_API_KEY is required; no request was sent.")
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    cases = [c for c in fixture["cases"] if "evidence" in c]
    OUT.mkdir(exist_ok=True)
    records = []
    for index, case in enumerate(cases, start=1):
        raw = None
        print(f"[{index}/{len(cases)}] synthetic case: {case['id']}", flush=True)
        record = {
            "case_id": case["id"],
            "mode": case["mode"],
            "expected_finding_type": case.get("expected_finding_type"),
            "must_preserve": case.get("must_preserve", []),
            "must_not": case.get("must_not", []),
            "model": MODEL,
            "candidate_status": "generated_not_human_reviewed",
        }
        try:
            raw, elapsed_ms, usage = call_model(case)
            record["raw_candidate_json"] = raw
            record["latency_ms"] = elapsed_ms
            record["usage"] = usage
            candidate = json.loads(raw)
            allowed_ids = {item["evidence_id"] for item in case["evidence"]}
            validated = validate_candidate_response(
                candidate, allowed_ids, mode=case["mode"], path="llm"
            )
            record["structural_validation"] = "passed"
            record["candidate"] = validated
        except Exception as exc:
            # Keep any returned synthetic candidate for review, but never accept
            # or display it. Do not persist request headers, credentials or bodies.
            record["structural_validation"] = "rejected"
            record["rejection_reason"] = f"{type(exc).__name__}: {str(exc)[:500]}"
            record["raw_candidate_json"] = raw
        try:
            record["deterministic_baseline"] = build_deterministic_response(
                case["evidence"],
                mode=case["mode"],
                missing_dimensions=case.get("missing_dimensions", []),
            )
        except Exception as exc:
            record["baseline_error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
        records.append(record)
        (OUT / "candidates.json").write_text(
            json.dumps({
                "status": "generated_not_human_reviewed",
                "provider": "groq",
                "model": MODEL,
                "records": records,
            }, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    summary = {
        "status": "generated_not_human_reviewed",
        "provider": "groq",
        "model": MODEL,
        "synthetic_case_count": len(records),
        "structurally_valid_count": sum(r["structural_validation"] == "passed" for r in records),
        "rejected_count": sum(r["structural_validation"] == "rejected" for r in records),
        "human_semantic_review": "required_not_completed",
        "production_release": "NO_GO",
        "records": records,
    }
    (OUT / "evaluation-report.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in summary.items() if k != "records"}, indent=2))

if __name__ == "__main__":
    main()
