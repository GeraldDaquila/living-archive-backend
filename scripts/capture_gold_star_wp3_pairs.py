#!/usr/bin/env python3
"""Capture attributable LLM and deterministic Guide outputs against one deployed source commit.

This is a bounded, manually reviewed calibration capture. It queries the secondary
mirror once per held-out question and executes the exact deployed deterministic
fallback locally from the same source commit. It never deploys or changes services.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
MIRROR = "https://living-archive-backend-mirror.onrender.com"
EVALUATION_SET = REPO_ROOT / "docs/qa/guide_learning_evaluation_set.json"


def _http_json(url: str, *, payload: dict | None = None, timeout: int = 45) -> dict:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method="GET" if data is None else "POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
            status = response.status
    except HTTPError as exc:
        raw, status = exc.read(), exc.code
    except (URLError, TimeoutError, OSError) as exc:
        return {"status": None, "error": f"{type(exc).__name__}: {exc}", "body": None}
    raw_text = raw.decode("utf-8", errors="replace")
    try:
        body = json.loads(raw_text)
    except json.JSONDecodeError:
        body = None
    return {
        "status": status,
        "error": None,
        "body": body,
        "raw_body": raw_text[:12000],
    }


def classify_llm_payload(body: dict | None) -> tuple[bool, dict]:
    """Require explicit final-answer LLM provenance; provider attempts alone are insufficient."""
    body = body if isinstance(body, dict) else {}
    provenance = body.get("response_provenance")
    provenance = provenance if isinstance(provenance, dict) else {}
    declared_class = str(provenance.get("class") or "").strip().casefold()
    provider = str(body.get("provider") or provenance.get("provider") or "").strip()
    model = str(body.get("model") or provenance.get("model") or "").strip()
    envelope = body.get("answer_envelope")
    envelope = envelope if isinstance(envelope, dict) else {}
    envelope_evidence = envelope.get("evidence")
    envelope_evidence = envelope_evidence if isinstance(envelope_evidence, dict) else {}
    envelope_route = envelope.get("route")
    envelope_route = envelope_route if isinstance(envelope_route, dict) else {}
    envelope_class = str(envelope_evidence.get("provenance_class") or "").strip().casefold()
    provider_present = envelope_route.get("provider_present") is True
    model_present = envelope_route.get("model_present") is True
    llm_invoked = provenance.get("llm_invoked") is True

    deterministic_markers = ("deterministic", "fallback", "recovery", "gold_standard_registry")
    is_deterministic = any(
        marker in (provider + " " + model + " " + declared_class + " " + envelope_class).casefold()
        for marker in deterministic_markers
    )
    explicit_llm = (
        declared_class in {"llm", "language_model", "model_generation"}
        and (llm_invoked or bool(provider and model))
    )
    envelope_llm = envelope_class in {"llm", "language_model", "model_generation"} and provider_present and model_present
    verified = bool((explicit_llm or envelope_llm) and not is_deterministic)
    metadata = {
        "declared_class": declared_class or None,
        "envelope_class": envelope_class or None,
        "provider": provider or None,
        "model": model or None,
        "provider_present": provider_present,
        "model_present": model_present,
        "llm_invoked": llm_invoked,
        "verification_basis": (
            "explicit_response_provenance"
            if explicit_llm else
            "answer_envelope_provenance"
            if envelope_llm and verified else
            "insufficient_or_deterministic_final_output_provenance"
        ),
    }
    return verified, metadata


def capture_deterministic_payload(main_module, query: str) -> dict:
    """Execute the deployed deterministic fallback and its shared visitor finalizer."""
    result = main_module._basic_inquiry_round1_deterministic_response(
        query, {}, {"context_blocks": ""}, recommendation_available=False
    )
    if isinstance(result, dict):
        raw_response = str(result.get("response") or "").strip()
        provider = str(result.get("provider") or "deterministic_fallback")
        model = str(result.get("model") or "")
        recommendation = result.get("recommendation")
    else:
        raw_response = str(result or "").strip()
        provider = "deterministic_registered_recovery"
        model = ""
        recommendation = None

    visitor_response = main_module._sanitize_basic_inquiry_response(raw_response)
    payload = {
        "ok": bool(visitor_response),
        "response": visitor_response,
        "recommendation": recommendation,
        "provider": provider,
        "model": model,
        "response_provenance": {
            "class": "deterministic_fallback",
            "provider": provider,
            "model": model,
        },
        "capture": {
            "path": "main._basic_inquiry_round1_deterministic_response",
            "raw_response": raw_response,
            "visitor_sanitized_response": visitor_response,
        },
    }
    finalized = main_module._guide_finalize_visitor_payload(payload, query)
    if not isinstance(finalized, dict):
        raise RuntimeError("Deterministic visitor finalizer returned a non-object payload.")
    finalized_response = str(finalized.get("response") or "").strip()
    if not finalized_response:
        raise RuntimeError("Deterministic visitor finalizer returned an empty answer.")
    finalized.setdefault("response_provenance", payload["response_provenance"])
    finalized.setdefault("capture", payload["capture"])
    return finalized


def verify_runtime_identity(base_url: str, expected_commit: str) -> dict:
    audit = _http_json(base_url.rstrip("/") + "/api/integration-audit")
    body = audit.get("body")
    if audit.get("status") != 200 or not isinstance(body, dict):
        raise RuntimeError(
            "Mirror integration audit unavailable: "
            f"status={audit.get('status')} error={audit.get('error')} "
            f"body={str(audit.get('raw_body') or '')[:1200]}"
        )
    # Integration health and deployment identity are separate facts. A missing
    # adapter can make the audit's overall ok flag false without invalidating
    # its independently reported immutable deployment SHA.
    deployed_commit = str(body.get("deployment_commit_sha") or "").strip()
    if not deployed_commit:
        raise RuntimeError("Mirror did not expose deployment_commit_sha; refusing unaligned capture.")
    if deployed_commit != expected_commit:
        raise RuntimeError(
            f"Source mismatch: mirror runs {deployed_commit}, local baseline is {expected_commit}; "
            "refusing to create a misleading pair."
        )
    return {
        "deployment_commit_sha": deployed_commit,
        "version": body.get("version"),
        "fingerprint": body.get("fingerprint"),
        "source_sha256": body.get("source_sha256"),
        "audit_contract": body.get("audit_contract"),
        "integration_audit_ok": body.get("ok") is True,
        "integration_audit_warnings": {
            "available_capabilities_missing_adapters": body.get("available_capabilities_missing_adapters") or [],
            "adapters_without_capabilities": body.get("adapters_without_capabilities") or [],
        },
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }


def _path_capture_metadata(runtime: dict, *, path: str, transport: dict | None = None, provenance: dict | None = None) -> dict:
    body = (transport or {}).get("body") or {}
    return {
        "path": path,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "runtime_identity": runtime,
        "request_id": body.get("request_id"),
        "transport_status": (transport or {}).get("status"),
        "transport_error": (transport or {}).get("error"),
        "provider_provenance": provenance or {},
        "processing": body.get("processing"),
        "route_source": body.get("route_source") or body.get("origin_route_source"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("WP3_CAPTURE_BASE_URL", MIRROR))
    parser.add_argument("--output", type=Path, default=Path("artifacts/gold-star-wp3-paired-capture.json"))
    parser.add_argument("--delay-seconds", type=float, default=0.5)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    if base_url != MIRROR:
        parser.error("WP3 capture is restricted to the secondary mirror; primary is not queried.")

    baseline_root = Path.cwd().resolve()
    sys.path.insert(0, str(REPO_ROOT))
    sys.path.insert(0, str(baseline_root))
    try:
        baseline_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=baseline_root, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("Could not identify the checked-out baseline commit.") from exc

    runtime = verify_runtime_identity(base_url, baseline_commit)

    # Import the exact source revision reported by the live mirror.
    import main as baseline_main
    from scripts.guide_live_evaluation import build_human_review_template, evaluate_held
    from scripts.gold_star_paired_offline_evaluation import evaluate_dataset

    suite = json.loads(EVALUATION_SET.read_text(encoding="utf-8"))
    rubric = suite["human_review_rubric"]
    records = []
    for index, case in enumerate(suite["cases"]):
        if index and args.delay_seconds > 0:
            time.sleep(args.delay_seconds)
        query = case["query"]
        transport = _http_json(base_url + "/api/query", payload={"query": query})
        live_body = transport.get("body") or {}
        verified_llm, llm_provenance = classify_llm_payload(live_body)

        llm_payload = None
        llm_checks = None
        if (
            verified_llm
            and transport.get("status") == 200
            and live_body.get("ok") is True
            and isinstance(live_body.get("response"), str)
            and live_body.get("response").strip()
        ):
            llm_payload = {
                "ok": live_body.get("ok") is True,
                "response": live_body["response"],
                "recommendation": live_body.get("recommendation"),
                "response_provenance": {
                    "class": "llm",
                    "provider": llm_provenance.get("provider"),
                    "model": llm_provenance.get("model"),
                    "verification_basis": llm_provenance["verification_basis"],
                },
                "capture": _path_capture_metadata(
                    runtime, path="mirror_POST_api_query", transport=transport,
                    provenance=llm_provenance,
                ),
            }
            llm_checks = evaluate_held(case, {
                "status": transport.get("status"), "error": transport.get("error"),
                "body": llm_payload,
            })

        deterministic_payload = capture_deterministic_payload(baseline_main, query)
        deterministic_payload["capture"] = {
            **(deterministic_payload.get("capture") or {}),
            **_path_capture_metadata(
                runtime, path="local_deployed_deterministic_fallback",
                provenance=deterministic_payload.get("response_provenance"),
            ),
            "transport_status": "local_function_execution",
        }
        deterministic_checks = evaluate_held(case, {
            "status": 200, "error": None, "body": deterministic_payload,
        })

        records.append({
            "case_id": case["case_id"],
            "question_type": case.get("question_type"),
            "query": query,
            "llm": llm_payload,
            "deterministic": deterministic_payload,
            "fixture_status": (
                "paired_llm_and_deterministic"
                if llm_payload is not None else
                "deterministic_captured_llm_path_unverified"
            ),
            "llm_capture_status": (
                "captured" if llm_payload is not None else
                "not_captured_unverified_path_or_transport"
            ),
            "llm_transport": {
                "status": transport.get("status"),
                "error": transport.get("error"),
                "request_id": live_body.get("request_id"),
                "provider_provenance": llm_provenance,
                "response_provenance": live_body.get("response_provenance"),
                "answer_envelope": live_body.get("answer_envelope"),
                "unverified_response": live_body.get("response") if llm_payload is None else None,
                "unverified_recommendation": live_body.get("recommendation") if llm_payload is None else None,
                "answer_basis": live_body.get("answer_basis"),
                "processing": live_body.get("processing"),
                "route_source": live_body.get("route_source") or live_body.get("origin_route_source"),
                "unverified_response_capture_status": (
                    "captured_unverified" if llm_payload is None and isinstance(live_body.get("response"), str)
                    else "not_available"
                ),
                "runtime_identity": runtime,
            },
            "heldout_checks": {
                "llm": llm_checks,
                "deterministic": deterministic_checks,
            },
            "human_review": {
                "llm": build_human_review_template(
                    rubric, applicable_critical=case.get("critical_dimensions")
                ) if llm_payload is not None else None,
                "deterministic": build_human_review_template(
                    rubric, applicable_critical=case.get("critical_dimensions")
                ),
            },
        })

    fixture = {
        "schema_version": "1.0",
        "dataset_id": "gold-star-heldout-seven-paired-fixture-capture",
        "purpose": "Actual held-out LLM and deterministic fallback outputs captured against one verified deployed source commit.",
        "source_capture_policy": "Only attributable runtime LLM outputs and actual deterministic function executions are populated. Missing or unverified LLM paths remain null. No authored or simulated response is accepted as a capture.",
        "runtime_identity": runtime,
        "source_code_commit": baseline_commit,
        "cases": [
            {
                "case_id": row["case_id"],
                "question_type": row["question_type"],
                "query": row["query"],
                "llm": row["llm"],
                "deterministic": row["deterministic"],
                "fixture_status": row["fixture_status"],
            }
            for row in records
        ],
    }
    paired_report = evaluate_dataset(fixture)
    report = {
        "report_schema_version": "1.0",
        "evaluation_mode": "verified_mirror_llm_plus_same_commit_local_deterministic_capture",
        "semantic_certification": False,
        "runtime_identity": runtime,
        "source_code_commit": baseline_commit,
        "paired_summary": {
            "cases_total": len(records),
            "llm_captured": sum(row["llm"] is not None for row in records),
            "deterministic_captured": sum(row["deterministic"] is not None for row in records),
            "paired_cases": paired_report["paired_cases"],
            "status_parity": paired_report["status_parity"],
            "status_disagreement": paired_report["status_disagreement"],
        },
        "paired_contract_evaluation": paired_report,
        "cases": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("WP3_PAIRED_CAPTURE_JSON_BEGIN")
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":")))
    print("WP3_PAIRED_CAPTURE_JSON_END")
    print(json.dumps(report["paired_summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
