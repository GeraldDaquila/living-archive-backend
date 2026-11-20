#!/usr/bin/env python3
"""Chromium visitor acceptance for the stewardship/consent relational contract on isolated QA."""
from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

CASES = [
    ("exact-relational-query", "What is the relationship between stewardship and consent?"),
    ("paraphrased-relational-query", "How do stewardship and consent relate in practice?"),
]
REQUIRED = (
    "entrusted responsibility",
    "does not automatically confer authority",
    "consultation alone",
    "informed, voluntary, and specific",
    "refusal or withdrawal",
    "ordinary act of care",
    "agency",
)
DOORWAY_TITLE = "Charter of the Living Archive | Purpose & Governance"
DOORWAY_URL = "https://geralddaquila.com/charter-of-the-living-archive/"
PROCESSING = "final_visitor_boundary_stewardship_consent_relational_contract"

def run(base_url: str, expected_sha: str) -> dict:
    from playwright.sync_api import sync_playwright
    base_url = base_url.rstrip("/")
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        root = page.goto(base_url, wait_until="domcontentloaded", timeout=90000)
        assert root is not None and root.status == 200, "QA root did not return HTTP 200"
        audit_response = page.request.get(base_url + "/api/integration-audit", timeout=90000)
        assert audit_response.status == 200, f"integration audit HTTP {audit_response.status}"
        audit = audit_response.json()
        assert audit.get("ok") is True, f"QA integration audit unhealthy: {audit}"
        actual_sha = str(audit.get("deployment_commit_sha") or "").strip()
        assert actual_sha == expected_sha, f"QA serves {actual_sha!r}, expected {expected_sha!r}"
        page.evaluate("""() => {
          document.body.innerHTML = '<main id="qa-visitor-harness"><h1>Stewardship and consent QA</h1><form id="query-form"><label for="question">Question</label><textarea id="question" required></textarea><button id="submit" type="submit">Ask</button></form><pre id="result" data-state="idle" data-payload=""></pre></main>';
          const form = document.querySelector("#query-form");
          const result = document.querySelector("#result");
          form.addEventListener("submit", async (event) => {
            event.preventDefault();
            result.dataset.state = "pending";
            result.dataset.payload = "";
            try {
              const response = await fetch("/api/query", {
                method: "POST",
                headers: {"Content-Type": "application/json", "Accept": "application/json"},
                body: JSON.stringify({query: document.querySelector("#question").value, history: []})
              });
              const body = await response.json();
              result.dataset.payload = JSON.stringify({status: response.status, body});
              result.dataset.state = "done";
            } catch (error) {
              result.dataset.payload = JSON.stringify({error: String(error)});
              result.dataset.state = "error";
            }
          });
        }""")
        for case_id, query in CASES:
            page.locator("#result").evaluate("(el) => { el.dataset.state = 'idle'; el.dataset.payload = ''; }")
            page.locator("#question").fill(query)
            page.locator("#submit").click()
            page.wait_for_function(
                "() => ['done','error'].includes(document.querySelector('#result')?.dataset.state)",
                timeout=120000,
            )
            captured = page.locator("#result").evaluate("(el) => JSON.parse(el.dataset.payload || '{}')")
            assert "error" not in captured, f"{case_id}: browser fetch failed: {captured}"
            body = captured.get("body") or {}
            answer = str(body.get("response") or body.get("answer") or "")
            folded = answer.casefold()
            missing = [phrase for phrase in REQUIRED if phrase not in folded]
            doorway = body.get("recommendation") or body.get("canonical_doorway") or {}
            title = doorway.get("title") or body.get("doorway_title")
            url = doorway.get("url") or body.get("doorway_url")
            checks = {
                "http_200": captured.get("status") == 200,
                "deployment_identity": body.get("deployment_commit_sha") == expected_sha,
                "relational_synthesis": not missing,
                "final_visitor_boundary": body.get("processing") == PROCESSING,
                "canonical_charter_doorway": title == DOORWAY_TITLE and url == DOORWAY_URL,
            }
            result = {
                "case_id": case_id, "query": query, "checks": checks,
                "missing_phrases": missing, "processing": body.get("processing"),
                "doorway_title": title, "doorway_url": url, "response": answer,
                "passed": all(checks.values()),
            }
            results.append(result)
            assert result["passed"], json.dumps(result, ensure_ascii=False)
        browser.close()
    return {
        "schema_version": "1.0",
        "acceptance_type": "real_chromium_same_origin_stewardship_consent_visitor_harness",
        "not_production_wordpress_ui": True,
        "target": base_url,
        "expected_commit": expected_sha,
        "runtime_identity": {"deployment_commit_sha": actual_sha, "integration_audit_ok": True},
        "browser": "Chromium",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "cases_total": len(results),
        "cases_passed": sum(item["passed"] for item in results),
        "cases_failed": sum(not item["passed"] for item in results),
        "cases": results,
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run(args.base_url, args.expected_commit)
    except Exception as exc:
        report = {
            "schema_version": "1.0",
            "acceptance_type": "real_chromium_same_origin_stewardship_consent_visitor_harness",
            "target": args.base_url,
            "expected_commit": args.expected_commit,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "fatal_error": {"type": type(exc).__name__, "message": str(exc)},
            "cases_total": 0, "cases_passed": 0, "cases_failed": 1, "cases": [],
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("cases_failed") == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
