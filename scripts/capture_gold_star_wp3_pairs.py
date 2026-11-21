#!/usr/bin/env python3
"""Capture attributable LLM and deterministic Guide outputs against one deployed source commit.

This is a bounded, manually reviewed calibration capture. It queries only the
USE2-Mirror secondary service through GitHub Actions and executes the exact deployed
deterministic fallback locally from the same source commit. It never targets the
primary service or any retired Standalone QA workspace.
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
APPROVED_TARGETS = {MIRROR}
EVALUATION_SET = REPO_ROOT / "docs/qa/guide_learning_evaluation_set.json"
PROVIDER_PROBE_QUERY = "Why can a well-designed policy still fail during implementation?"


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


def classify_deterministic_payload(body: dict | None) -> tuple[bool, dict]:
    """Accept a real visitor response as deterministic only when provenance says no LLM ran."""
    body = body if isinstance(body, dict) else {}
    provenance = body.get("response_provenance")
    provenance = provenance if isinstance(provenance, dict) else {}
    declared_class = str(provenance.get("class") or "").strip().casefold()
    llm_invoked = provenance.get("llm_invoked")
    response = body.get("response")
    deterministic_markers = ("deterministic", "fallback", "recovery", "gold_standard_registry")
    declared_deterministic = any(marker in declared_class for marker in deterministic_markers)
    verified = (
        isinstance(response, str)
        and bool(response.strip())
        and llm_invoked is False
        and not classify_llm_payload(body)[0]
    )
    return verified, {
        "declared_class": declared_class or None,
        "llm_invoked": llm_invoked,
        "declared_deterministic": declared_deterministic,
        "verification_basis": (
            "explicit_no_llm_invocation_at_visitor_boundary"
            if verified else "insufficient_final_output_provenance"
        ),
    }


def capture_live_deterministic_payload(body: dict, runtime: dict, transport: dict) -> dict:
    """Preserve the exact visitor response when the runtime proves no LLM was invoked."""
    provenance = body.get("response_provenance")
    provenance = provenance if isinstance(provenance, dict) else {}
    response = str(body.get("response") or "").strip()
    if not response:
        raise RuntimeError("Live deterministic visitor capture returned an empty answer.")
    provider = str(body.get("provider") or provenance.get("provider") or "visitor_deterministic")
    model = str(body.get("model") or provenance.get("model") or "")
    return {
        "ok": body.get("ok") is True,
        "response": response,
        "recommendation": body.get("recommendation"),
        "provider": provider,
        "model": model,
        "response_provenance": dict(provenance),
        "capture": {
            **_path_capture_metadata(
                runtime,
                path="standalone_qa_POST_api_query_deterministic_visitor_output",
                transport=transport,
                provenance=provenance,
            ),
            "raw_response": response,
            "visitor_sanitized_response": response,
            "answer_envelope": body.get("answer_envelope"),
        },
        "route_source": body.get("route_source") or body.get("origin_route_source"),
        "processing": body.get("processing"),
    }


def capture_deterministic_payload(main_module, query: str) -> dict:
    """Execute the same provider-independent deterministic path used by visitors."""
    result = None
    capture_path = ""
    preserve_no_doorway = False

    task_recovery_fn = getattr(main_module, "_compose_task_specific_recovery", None)
    task_recovery = task_recovery_fn(query) if callable(task_recovery_fn) else None
    if isinstance(task_recovery, dict) and str(task_recovery.get("response") or "").strip():
        result = {
            "response": task_recovery["response"],
            "recommendation": None,
            "provider": str(task_recovery.get("recovery_id") or "task_specific_deterministic_recovery"),
            "model": "",
        }
        capture_path = "main._compose_task_specific_recovery"
        preserve_no_doorway = True
    else:
        fact_recovery_fn = getattr(main_module, "_established_general_knowledge_recovery", None)
        fact_recovery = fact_recovery_fn(query) if callable(fact_recovery_fn) else None
        if isinstance(fact_recovery, dict) and str(fact_recovery.get("response") or "").strip():
            result = {
                "response": fact_recovery["response"],
                "recommendation": fact_recovery.get("doorway"),
                "provider": str(fact_recovery.get("fact_id") or "registered_general_knowledge_recovery"),
                "model": "",
            }
            capture_path = "main._established_general_knowledge_recovery"
            preserve_no_doorway = not bool(fact_recovery.get("doorway"))
        else:
            trust_contract_fn = getattr(main_module, "_trust_community_stewardship_final_contract", None)
            trust_contract = trust_contract_fn(query) if callable(trust_contract_fn) else None
            if isinstance(trust_contract, dict) and str(trust_contract.get("response") or "").strip():
                result = {
                    "response": trust_contract["response"],
                    "recommendation": trust_contract.get("recommendation"),
                    "provider": "bounded_trust_community_stewardship_recovery",
                    "model": "",
                }
                capture_path = "main._trust_community_stewardship_final_contract"

    if result is None:
        result = main_module._basic_inquiry_round1_deterministic_response(
            query, {}, {"context_blocks": ""}, recommendation_available=False
        )
        capture_path = "main._basic_inquiry_round1_deterministic_response"

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
            "class": "deterministic_recovery",
            "provider": provider,
            "model": model,
            "llm_invoked": False,
        },
        "capture": {
            "path": capture_path,
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
    if preserve_no_doorway:
        # The visitor's early task/fact routes intentionally return no doorway.
        # The shared finalizer may infer a broad fallback; do not let the capture
        # harness invent a doorway that the actual visitor route did not emit.
        finalized["recommendation"] = None
        finalized["canonical_doorway"] = None
        finalized["doorway_title"] = None
        finalized["doorway_url"] = None
        finalized["doorway_omission_reason"] = "no_direct_archive_continuation"
    return finalized


def verify_runtime_identity(base_url: str, expected_commit: str) -> dict:
    # The secondary mirror may be cold-starting on its Render instance. Retry only
    # transport failures and transient 5xx responses; never retry or bypass a
    # valid identity response that reports a different deployment commit.
    audit = None
    for attempt in range(3):
        audit = _http_json(
            base_url.rstrip("/") + "/api/integration-audit",
            timeout=90,
        )
        body = audit.get("body")
        if audit.get("status") == 200 and isinstance(body, dict):
            break
        status = audit.get("status")
        transient = status is None or (isinstance(status, int) and status >= 500)
        if not transient or attempt == 2:
            break
        time.sleep(5)
    body = audit.get("body") if isinstance(audit, dict) else None
    if audit.get("status") != 200 or not isinstance(body, dict):
        raise RuntimeError(
            "Target integration audit unavailable after bounded retries: "
            f"status={audit.get('status')} error={audit.get('error')} "
            f"body={str(audit.get('raw_body') or '')[:1200]}"
        )
    # Integration health and deployment identity are separate facts. A missing
    # adapter can make the audit's overall ok flag false without invalidating
    # its independently reported immutable deployment SHA.
    deployed_commit = str(body.get("deployment_commit_sha") or "").strip()
    if not deployed_commit:
        raise RuntimeError("Target did not expose deployment_commit_sha; refusing unaligned capture.")
    if deployed_commit != expected_commit:
        raise RuntimeError(
            f"Source mismatch: target runs {deployed_commit}, local baseline is {expected_commit}; "
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


def wait_for_runtime_identity(base_url: str, expected_commit: str, timeout_seconds: int = 0) -> dict:
    """Wait for the explicitly expected secondary-mirror deployment; never capture against a stale SHA."""
    if timeout_seconds < 0:
        raise ValueError("timeout_seconds must be zero or greater.")
    deadline = time.monotonic() + timeout_seconds
    last_error = None
    while True:
        try:
            return verify_runtime_identity(base_url, expected_commit)
        except RuntimeError as exc:
            last_error = exc
            if timeout_seconds == 0:
                raise
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError(
                    f"Timed out waiting for USE2-Mirror commit {expected_commit}: {last_error}"
                ) from last_error
            # A valid but old SHA means Render has not finished the explicitly
            # triggered mirror deployment. Keep waiting only within this bounded
            # window; never issue visitor queries while it is stale.
            time.sleep(min(10, remaining))


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


def select_evaluation_cases(cases: list[dict], requested_case_ids: list[str] | None = None) -> list[dict]:
    """Select unique held-out case IDs while preserving the requested order."""
    if not requested_case_ids:
        return list(cases)
    if len(set(requested_case_ids)) != len(requested_case_ids):
        raise ValueError("Duplicate --case-id values are not allowed.")
    by_id = {str(case.get("case_id") or ""): case for case in cases}
    missing = [case_id for case_id in requested_case_ids if case_id not in by_id]
    if missing:
        raise ValueError("Unknown held-out case ID(s): " + ", ".join(missing))
    return [by_id[case_id] for case_id in requested_case_ids]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("WP3_CAPTURE_BASE_URL", MIRROR))
    parser.add_argument("--output", type=Path, default=Path("artifacts/gold-star-wp3-paired-capture.json"))
    parser.add_argument("--delay-seconds", type=float, default=0.5)
    parser.add_argument(
        "--identity-wait-seconds",
        type=int,
        default=0,
        help="Bounded wait for USE2-Mirror to finish deploying this exact checked-out commit.",
    )
    parser.add_argument(
        "--min-llm-captures",
        type=int,
        default=0,
        help="Fail after saving the report if fewer attributable LLM outputs are captured.",
    )
    parser.add_argument("--case-id", action="append", dest="case_ids", help="Capture only this held-out case ID; may be repeated.")
    parser.add_argument("--skip-provider-probe", action="store_true", help="Skip the separate provider probe for a bounded single-case diagnostic.")
    args = parser.parse_args()
    if args.min_llm_captures < 0:
        parser.error("--min-llm-captures must be zero or greater.")
    if args.identity_wait_seconds < 0:
        parser.error("--identity-wait-seconds must be zero or greater.")

    base_url = args.base_url.rstrip("/")
    if base_url not in APPROVED_TARGETS:
        parser.error(
            "WP3 capture is restricted to USE2-Mirror; the primary, retired Standalone QA, "
            "and arbitrary hosts are never queried."
        )
    target_kind = "secondary_mirror"

    baseline_root = Path.cwd().resolve()
    sys.path.insert(0, str(REPO_ROOT))
    sys.path.insert(0, str(baseline_root))
    try:
        baseline_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=baseline_root, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("Could not identify the checked-out baseline commit.") from exc

    runtime = wait_for_runtime_identity(base_url, baseline_commit, args.identity_wait_seconds)

    # Import the exact source revision reported by the live mirror.
    import main as baseline_main
    from scripts.guide_live_evaluation import build_human_review_template, evaluate_held
    from scripts.gold_star_paired_offline_evaluation import evaluate_dataset

    suite = json.loads(EVALUATION_SET.read_text(encoding="utf-8"))
    rubric = suite["human_review_rubric"]
    try:
        selected_cases = select_evaluation_cases(suite["cases"], args.case_ids)
    except ValueError as exc:
        parser.error(str(exc))
    records = []
    for index, case in enumerate(selected_cases):
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
                    runtime, path=f"{target_kind}_POST_api_query", transport=transport,
                    provenance=llm_provenance,
                ),
            }
            llm_checks = evaluate_held(case, {
                "status": transport.get("status"), "error": transport.get("error"),
                "body": llm_payload,
            })

        deterministic_verified, deterministic_provenance = classify_deterministic_payload(live_body)
        if deterministic_verified and transport.get("status") == 200 and live_body.get("ok") is True:
            # The actual visitor boundary is authoritative. Do not score a local
            # generic fallback in place of a task-specific deterministic response
            # that the deployed service really returned.
            deterministic_payload = capture_live_deterministic_payload(live_body, runtime, transport)
            deterministic_payload["capture"]["deterministic_provenance_verification"] = deterministic_provenance
        else:
            deterministic_payload = capture_deterministic_payload(baseline_main, query)
            deterministic_payload["capture"] = {
                **(deterministic_payload.get("capture") or {}),
                **_path_capture_metadata(
                    runtime, path="local_same_commit_deterministic_fallback",
                    provenance=deterministic_payload.get("response_provenance"),
                ),
                "transport_status": "local_function_execution",
                "deterministic_provenance_verification": deterministic_provenance,
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
                "deterministic_visitor_captured_llm_unverified"
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

    if args.skip_provider_probe:
        provider_probe = {
            "query": None,
            "transport_status": None,
            "transport_error": None,
            "request_id": None,
            "response_provenance": None,
            "provider_provenance": {"verification_basis": "skipped_by_request"},
            "attributable_llm": False,
            "llm": None,
            "unverified_response": None,
            "route_source": None,
            "processing": None,
            "human_review": None,
            "skipped": True,
            "skip_reason": "explicit_single_case_diagnostic",
        }
    else:
        # The held-out suite intentionally includes deterministic task routes.
        # Exercise one separate ordinary question so provider attribution is tested
        # rather than inferred from cases that correctly bypass the LLM.
        provider_probe_transport = _http_json(
            base_url + "/api/query",
            payload={"query": PROVIDER_PROBE_QUERY},
        )
        provider_probe_body = provider_probe_transport.get("body") or {}
        provider_probe_llm_verified, provider_probe_provenance = classify_llm_payload(provider_probe_body)
        provider_probe_llm = None
        if (
            provider_probe_llm_verified
            and provider_probe_transport.get("status") == 200
            and provider_probe_body.get("ok") is True
            and isinstance(provider_probe_body.get("response"), str)
            and provider_probe_body.get("response").strip()
        ):
            provider_probe_llm = {
                "ok": True,
                "response": provider_probe_body["response"],
                "recommendation": provider_probe_body.get("recommendation"),
                "response_provenance": {
                    "class": "llm",
                    "provider": provider_probe_provenance.get("provider"),
                    "model": provider_probe_provenance.get("model"),
                    "verification_basis": provider_probe_provenance["verification_basis"],
                },
                "capture": _path_capture_metadata(
                    runtime,
                    path=f"{target_kind}_POST_api_query_provider_probe",
                    transport=provider_probe_transport,
                    provenance=provider_probe_provenance,
                ),
            }
        provider_probe = {
            "query": PROVIDER_PROBE_QUERY,
            "transport_status": provider_probe_transport.get("status"),
            "transport_error": provider_probe_transport.get("error"),
            "request_id": provider_probe_body.get("request_id"),
            "response_provenance": provider_probe_body.get("response_provenance"),
            "provider_provenance": provider_probe_provenance,
            "attributable_llm": provider_probe_llm is not None,
            "llm": provider_probe_llm,
            "unverified_response": (
                provider_probe_body.get("response") if provider_probe_llm is None else None
            ),
            "route_source": provider_probe_body.get("route_source") or provider_probe_body.get("origin_route_source"),
            "processing": provider_probe_body.get("processing"),
            "human_review": build_human_review_template(rubric) if provider_probe_llm is not None else None,
            "skipped": False,
        }

    fixture = {
        "schema_version": "1.0",
        "dataset_id": "gold-star-heldout-paired-fixture-capture",
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
        "evaluation_mode": "verified_secondary_mirror_llm_plus_same_commit_local_deterministic_capture",
        "selected_case_ids": [row["case_id"] for row in records],
        "provider_probe_skipped": args.skip_provider_probe,
        "semantic_certification": False,
        "runtime_identity": runtime,
        "source_code_commit": baseline_commit,
        "paired_summary": {
            "cases_total": len(records),
            "llm_captured": sum(row["llm"] is not None for row in records),
            "provider_probe_llm_attributed": provider_probe["attributable_llm"],
            "llm_captured_total": sum(row["llm"] is not None for row in records) + int(provider_probe["attributable_llm"]),
            "deterministic_captured": sum(row["deterministic"] is not None for row in records),
            "paired_cases": paired_report["paired_cases"],
            "status_parity": paired_report["status_parity"],
            "status_disagreement": paired_report["status_disagreement"],
        },
        "paired_contract_evaluation": paired_report,
        "provider_probe": provider_probe,
        "cases": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("WP3_PAIRED_CAPTURE_JSON_BEGIN")
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":")))
    print("WP3_PAIRED_CAPTURE_JSON_END")
    print(json.dumps(report["paired_summary"], indent=2))
    if report["paired_summary"]["llm_captured_total"] < args.min_llm_captures:
        print(
            "Insufficient attributable LLM captures across held-out cases and provider probe: "
            f"{report['paired_summary']['llm_captured_total']} < {args.min_llm_captures}",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
