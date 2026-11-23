#!/usr/bin/env python3
"""Capture same-provider, same-model Gold Star control/treatment pairs locally.

The candidate application is exercised through its complete ASGI visitor boundary.
No Render service is deployed or queried. Outputs are synthetic evaluation material;
the blind review package and unblinding key are emitted separately.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import random
import subprocess
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CASE_SET_PATH = ROOT / "docs" / "qa" / "gold_star_matched_pair_cases.json"
TARGET_LESSON_ID = "gs-2026-11-23-community-rule-design-liberty-shared-obligations"
CASE_IDS = (
    "heldout-community-rule-design-transfer-001",
    "heldout-policy-implementation-001",
    "heldout-thermal-conductivity-001",
)
CAPTURE_CONTEXT: ContextVar[dict[str, Any] | None] = ContextVar(
    "gold_star_matched_pair_capture", default=None
)


def _sha256(value: bytes | str) -> str:
    raw = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(raw).hexdigest()


def _git_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def _install_observers(composition):
    """Record only approved lesson IDs and adjudication metadata, never hidden reasoning."""
    original_contribution = composition._gold_star_active_quality_contribution
    original_normalizer = composition._normalize_gold_star_provider_adjudication

    def observe_contribution(query):
        result = original_contribution(query)
        state = CAPTURE_CONTEXT.get()
        if state is not None and isinstance(result, dict):
            state["retrieved_candidates"] = [
                {
                    "benchmark_id": str(item.get("benchmark_id") or ""),
                    "role": str(item.get("role") or ""),
                    "activation_condition": str(item.get("activation_condition") or ""),
                }
                for item in result.get("candidates", [])
                if isinstance(item, dict)
            ]
        return result

    def observe_adjudication(value, *, response, candidates):
        result = original_normalizer(value, response=response, candidates=candidates)
        state = CAPTURE_CONTEXT.get()
        if state is not None:
            state["provider_adjudication"] = {
                "status": result.get("status"),
                "selected_candidate_ids": list(result.get("selected_candidate_ids") or []),
                "rejection_reason_codes": list(result.get("rejection_reason_codes") or []),
                "application_evidence_present": bool(result.get("application_evidence_present")),
                "application_evidence_candidate_ids": list(
                    result.get("application_evidence_candidate_ids") or []
                ),
                "application": str(result.get("application") or "not_observed"),
            }
        return result

    composition._gold_star_active_quality_contribution = observe_contribution
    composition._normalize_gold_star_provider_adjudication = observe_adjudication

    def restore():
        composition._gold_star_active_quality_contribution = original_contribution
        composition._normalize_gold_star_provider_adjudication = original_normalizer

    return restore


def _load_cases():
    suite = json.loads(CASE_SET_PATH.read_text(encoding="utf-8"))
    by_id = {item["case_id"]: item for item in suite.get("cases", [])}
    missing = [case_id for case_id in CASE_IDS if case_id not in by_id]
    if missing:
        raise RuntimeError("Held-out evaluation cases missing: " + ", ".join(missing))
    return suite, [by_id[case_id] for case_id in CASE_IDS]


def _safe_provider_identity(payload: dict) -> tuple[str, str, bool]:
    provenance = payload.get("response_provenance")
    provenance = provenance if isinstance(provenance, dict) else {}
    return (
        str(provenance.get("provider") or payload.get("provider") or "").strip(),
        str(provenance.get("model") or payload.get("model") or "").strip(),
        bool(str(provenance.get("provider") or payload.get("provider") or "").strip())
        and bool(str(provenance.get("model") or payload.get("model") or "").strip())
        and provenance.get("llm_invoked") is True
        and str(provenance.get("class") or "").casefold() in {
            "llm", "language_model", "model_generation"
        },
    )


async def _request_arm(client, evaluation_context, provider, model, query, arm):
    import httpx

    state: dict[str, Any] = {
        "retrieved_candidates": [],
        "provider_adjudication": {
            "status": "not_observed",
            "selected_candidate_ids": [],
            "rejection_reason_codes": [],
            "application_evidence_present": False,
            "application_evidence_candidate_ids": [],
            "application": "not_observed",
        },
    }
    token = CAPTURE_CONTEXT.set(state)
    try:
        try:
            with evaluation_context(arm=arm, provider=provider, model=model):
                response = await client.post("/api/query", json={"query": query})
            status_code = response.status_code
            try:
                payload = response.json()
            except ValueError:
                payload = {}
            error_type = None
        except httpx.HTTPError as exc:
            status_code = None
            payload = {}
            error_type = type(exc).__name__
        if not isinstance(payload, dict):
            payload = {}
        actual_provider, actual_model, llm_invoked = _safe_provider_identity(payload)
        return {
            "http_status": status_code,
            "transport_error_type": error_type,
            "ok": payload.get("ok") is True,
            "response": str(payload.get("response") or ""),
            "request_id": str(payload.get("request_id") or ""),
            "provider": actual_provider,
            "model": actual_model,
            "llm_invoked": llm_invoked,
            "response_provenance": payload.get("response_provenance") or {},
            "answer_envelope": payload.get("answer_envelope"),
            "retrieved_candidates": state["retrieved_candidates"],
            "provider_adjudication": state["provider_adjudication"],
            "route_source": payload.get("route_source"),
            "deployment_commit_sha": payload.get("deployment_commit_sha"),
        }
    finally:
        CAPTURE_CONTEXT.reset(token)


async def capture(args) -> dict:
    import httpx
    import main
    import general_guide_composition as composition
    import provider_bank
    import gold_star_lessons
    from gold_star_evaluation_context import evaluation_context
    from general_guide_composition import CONTRACT_VERSION as COMPOSITION_CONTRACT_VERSION

    suite, cases = _load_cases()
    runtime_commit = _git_sha()
    registry_bytes = (
        ROOT / "docs" / "qa" / "gold_standard_registry.json"
    ).read_bytes()
    registry_sha = _sha256(registry_bytes)

    negative_control_query = (
        "Why does a metal spoon feel colder than a wooden spoon when both are at the same room temperature?"
    )
    negative_control_candidates = gold_star_lessons.select_lesson_candidates(
        negative_control_query, limit=4
    )
    negative_control_ids = [
        str(item.get("benchmark_id") or "")
        for item in negative_control_candidates
        if isinstance(item, dict)
    ]
    negative_control_passed = TARGET_LESSON_ID not in negative_control_ids

    eligible = provider_bank.select(
        main.use_core, operation="general_guide_composition"
    )
    if not eligible:
        raise RuntimeError(
            "No eligible provider/model is configured in this GitHub Actions runner. "
            "Configure an approved provider credential as a repository or environment secret."
        )
    provider = str(eligible[0].get("provider") or "").strip()
    model = str(eligible[0].get("model") or "").strip()
    if not provider or not model:
        raise RuntimeError("Provider bank returned an incomplete provider/model identity.")

    restore = _install_observers(composition)
    records = []
    blind_cases = []
    unblinding = {}
    generation_config = {
        "operation": "general_guide_composition",
        "max_tokens": 750,
        "provider": provider,
        "model": model,
        "evaluation_retry_policy": "one exact pinned provider/model; no alternate lane",
    }
    generation_fingerprint = _sha256(
        json.dumps(generation_config, sort_keys=True, separators=(",", ":"))
    )

    try:
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://gold-star-evaluation.local",
            timeout=httpx.Timeout(args.timeout_seconds),
        ) as client:
            for case in cases:
                arms = {}
                for arm in ("control", "treatment"):
                    arms[arm] = await _request_arm(
                        client, evaluation_context, provider, model, case["query"], arm
                    )

                control, treatment = arms["control"], arms["treatment"]
                failures = []
                for arm_name, result in arms.items():
                    if result["http_status"] != 200 or not result["ok"] or not result["response"].strip():
                        failures.append(f"{arm_name}_visitor_response_invalid")
                    if not result["llm_invoked"]:
                        failures.append(f"{arm_name}_not_attributable_llm")
                    if result["provider"] != provider or result["model"] != model:
                        failures.append(f"{arm_name}_provider_model_pin_mismatch")
                if control["retrieved_candidates"]:
                    failures.append("control_exposed_gold_star_guidance")

                target_in_treatment = any(
                    item["benchmark_id"] == TARGET_LESSON_ID
                    for item in treatment["retrieved_candidates"]
                )
                target_selected = TARGET_LESSON_ID in (
                    treatment["provider_adjudication"]["selected_candidate_ids"]
                )
                target_span = TARGET_LESSON_ID in (
                    treatment["provider_adjudication"]["application_evidence_candidate_ids"]
                )
                if not target_in_treatment:
                    failures.append("community_rule_gold_star_not_retrieved")
                if not target_selected:
                    failures.append("community_rule_gold_star_not_selected_by_provider")
                if not target_span:
                    failures.append("community_rule_application_span_not_observed")
                if not negative_control_passed:
                    failures.append("community_rule_gold_star_cross_domain_selector_leak")

                case_family = str(case.get("question_type") or case["case_id"])
                # This is a fingerprint of the shared, non-adaptive request contract.
                # The actual treatment prompt is intentionally different because it
                # contains the approved lesson's structural guidance.
                base_system_prompt = composition._build_general_guide_system_message(
                    case["query"], has_gold_star_guidance=False,
                    gold_star_quality_instruction="",
                )
                base_prompt_fingerprint = _sha256(
                    base_system_prompt + "\\n\\nVISITOR_QUESTION\\n" + case["query"]
                )

                record = {
                    "case_id": case["case_id"],
                    "case_family": case_family,
                    "question": case["query"],
                    "critical_dimensions": list(case.get("critical_dimensions") or []),
                    "runtime_commit": runtime_commit,
                    "composition_contract_version": COMPOSITION_CONTRACT_VERSION,
                    "provider": provider,
                    "model": model,
                    "base_prompt_fingerprint": base_prompt_fingerprint,
                    "generation_config_fingerprint": generation_fingerprint,
                    "gold_star_registry_sha256": registry_sha,
                    "captured_at": datetime.now(timezone.utc).isoformat(),
                    "control": control,
                    "treatment": treatment,
                    "acceptance": {
                        "passed": not failures,
                        "failures": failures,
                        "community_rule_candidate_retrieved": target_in_treatment,
                        "community_rule_candidate_selected": target_selected,
                        "community_rule_application_span_observed": target_span,
                        "semantic_application_certified": False,
                    },
                }
                records.append(record)

                labels = ["A", "B"]
                random.SystemRandom().shuffle(labels)
                label_for_arm = {"control": labels[0], "treatment": labels[1]}
                unblinding[case["case_id"]] = {
                    label_for_arm["control"]: "control",
                    label_for_arm["treatment"]: "treatment",
                }
                blind_cases.append({
                    "case_id": case["case_id"],
                    "case_family": case_family,
                    "question": case["query"],
                    "critical_dimensions": list(case.get("critical_dimensions") or []),
                    "rubric": list(case.get("rubric") or []),
                    "responses": {
                        label_for_arm["control"]: control["response"],
                        label_for_arm["treatment"]: treatment["response"],
                    },
                    "review_instruction": (
                        "Score Response A and Response B independently while blinded. "
                        "Use the supplied 0-2 rubric and hard gates; do not infer which "
                        "response received adaptive guidance."
                    ),
                })
    finally:
        restore()

    return {
        "schema_version": "1.0",
        "evaluation_mode": "local_candidate_same_provider_model_paired_generation",
        "semantic_certification": False,
        "runtime_commit": runtime_commit,
        "provider": provider,
        "model": model,
        "composition_contract_version": COMPOSITION_CONTRACT_VERSION,
        "gold_star_registry_sha256": registry_sha,
        "selector_negative_control": {
            "query": negative_control_query,
            "selected_candidate_ids": negative_control_ids,
            "community_rule_gold_star_excluded": negative_control_passed,
            "semantic_certification": False,
        },
        "case_count": len(records),
        "case_family_count": len({item["case_family"] for item in records}),
        "passed_case_count": sum(item["acceptance"]["passed"] for item in records),
        "failed_case_count": sum(not item["acceptance"]["passed"] for item in records),
        "cases": records,
        "interpretation": (
            "This artifact proves only candidate-local matched generation, exact provider "
            "attribution, bounded lesson retrieval, provider-reported selection, and exact "
            "answer-span presence. It does not certify semantic application or improvement. "
            "Blind human review and gold_star_adaptation_evaluation.py remain mandatory."
        ),
        "human_review_template": {
            "policy": "Complete blind scoring before consulting the separate unblinding key.",
            "scale": {
                "0": "Fails, contradicts the criterion, or materially misleads.",
                "1": "Partially satisfies; a meaningful weakness remains.",
                "2": "Clearly satisfies the criterion.",
                "NA": "Not applicable; reviewer must record a controlled reason.",
            },
            "dimensions": [
                {"id": dimension, "guidance": "Score this dimension against the case-specific rubric."}
                for dimension in sorted({
                    "answer_directness", "factual_accuracy", "archive_grounding_and_provenance",
                    "cosmology_fidelity", "human_voice_and_respect", "sentence_coherence",
                    "paragraph_purpose_and_concision", "response_proportionality",
                    "fractal_coherence", "uncertainty_honesty", "doorway_relevance_and_timing",
                    "visitor_orientation",
                } | {
                    dimension for item in cases for dimension in item.get("critical_dimensions", [])
                })
            ],
            "hard_gates": ["safety", "evidence_integrity", "epistemic_calibration"],
            "critical_dimensions_by_case": {
                item["case_id"]: item["critical_dimensions"] for item in cases
            },
        },
        "_blind_review_cases": blind_cases,
        "_unblinding_key": unblinding,
    }


def main_cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/gold-star-matched-pairs"))
    parser.add_argument("--timeout-seconds", type=float, default=90.0)
    args = parser.parse_args()
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be greater than zero.")

    report = asyncio.run(capture(args))
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    blind_cases = report.pop("_blind_review_cases")
    unblinding_key = report.pop("_unblinding_key")
    (output_dir / "matched-pair-evidence.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "blind-review-package.json").write_text(
        json.dumps({
            "schema_version": "1.0",
            "blind": True,
            "cases": blind_cases,
            "scoring_scale": report["human_review_template"]["scale"],
            "hard_gates": report["human_review_template"]["hard_gates"],
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "unblinding-key.json").write_text(
        json.dumps(unblinding_key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    summary = {
        key: report[key] for key in (
            "runtime_commit", "provider", "model", "case_count",
            "passed_case_count", "failed_case_count",
        )
    }
    print(json.dumps(summary, indent=2))
    return 0 if report["failed_case_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main_cli())
