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
    "heldout-community-rule-necessity-002",
    "heldout-community-rule-burdens-003",
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


def _install_observers(composition, main_module):
    """Observe Gold Star application while isolating unrelated auxiliary provider work."""
    original_contribution = composition._gold_star_active_quality_contribution
    original_normalizer = composition._normalize_gold_star_provider_adjudication
    original_route = composition.route_with_model_bank
    original_system_builder = composition._build_general_guide_system_message
    original_claim_adjudication = main_module._adjudicate_final_visitor_claims

    def observe_system_builder(question, **kwargs):
        system_message = original_system_builder(question, **kwargs)
        state = CAPTURE_CONTEXT.get()
        if state is not None:
            # Rebuild the same request's non-adaptive base contract by removing
            # only the two explicit treatment switches. This verifies that the
            # arms differ by the governed Gold Star contribution, not by an
            # unrelated question/context/system-contract change.
            base_kwargs = dict(kwargs)
            base_kwargs["has_gold_star_guidance"] = False
            base_kwargs["gold_star_quality_instruction"] = ""
            base_system_message = original_system_builder(question, **base_kwargs)
            state["base_system_prompt_sha256"] = _sha256(base_system_message)
        return system_message

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

    def suppress_auxiliary_claim_adjudication(*args, **kwargs):
        state = CAPTURE_CONTEXT.get()
        if state is None:
            return original_claim_adjudication(*args, **kwargs)
        state["auxiliary_claim_adjudication"] = {
            "status": "not_run",
            "reason": "isolated_matched_pair_composition_provider_budget",
        }
        return {
            "version": "1.0",
            "status": "unassessed",
            "reason": "isolated_matched_pair_composition_provider_budget",
            "claims": [],
            "claim_count": 0,
        }

    def observe_route(**kwargs):
        state = CAPTURE_CONTEXT.get()
        if state is not None:
            messages = kwargs.get("messages")
            if isinstance(messages, list) and len(messages) >= 2:
                system_message = messages[0] if isinstance(messages[0], dict) else {}
                user_message = messages[-1] if isinstance(messages[-1], dict) else {}
                state["route_input_system_prompt_sha256"] = _sha256(
                    str(system_message.get("content") or "")
                )
                state["user_content_sha256"] = _sha256(
                    str(user_message.get("content") or "")
                )
            state["route_operation"] = str(kwargs.get("operation") or "")
            state["max_tokens"] = kwargs.get("max_tokens")
            schema = kwargs.get("schema")
            state["schema_sha256"] = (
                _sha256(json.dumps(schema, sort_keys=True, separators=(",", ":")))
                if isinstance(schema, dict) else None
            )
            state["schema_mode"] = schema.get("mode") if isinstance(schema, dict) else None
        return original_route(**kwargs)

    composition._gold_star_active_quality_contribution = observe_contribution
    composition._normalize_gold_star_provider_adjudication = observe_adjudication
    composition.route_with_model_bank = observe_route
    composition._build_general_guide_system_message = observe_system_builder
    main_module._adjudicate_final_visitor_claims = suppress_auxiliary_claim_adjudication

    def restore():
        composition._gold_star_active_quality_contribution = original_contribution
        composition._normalize_gold_star_provider_adjudication = original_normalizer
        composition.route_with_model_bank = original_route
        composition._build_general_guide_system_message = original_system_builder
        main_module._adjudicate_final_visitor_claims = original_claim_adjudication

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
    provider = str(provenance.get("provider") or payload.get("provider") or "").strip()
    model = str(provenance.get("model") or payload.get("model") or "").strip()
    identity = (provider + " " + model).casefold()
    deterministic_markers = (
        "deterministic", "fallback", "recovery", "gold_standard_registry",
        "extractive", "approved-reference",
    )
    attributable = (
        bool(provider)
        and bool(model)
        and provenance.get("llm_invoked") is True
        and str(provenance.get("class") or "").casefold() in {
            "llm", "language_model", "model_generation"
        }
        and not any(marker in identity for marker in deterministic_markers)
    )
    return provider, model, bool(attributable)


def _choose_provider_candidate(eligible: list[dict], provider: str = "", model: str = "") -> dict:
    """Choose one exact eligible provider/model pair; never silently substitute."""
    provider = str(provider or "").strip()
    model = str(model or "").strip()
    if bool(provider) != bool(model):
        raise ValueError("Both --provider and --model must be supplied together.")
    if provider and model:
        candidate = next((
            item for item in eligible
            if str(item.get("provider") or "").strip() == provider
            and str(item.get("model") or "").strip() == model
        ), None)
        if candidate is None:
            raise RuntimeError(
                f"The pinned provider/model is not eligible for this operation: {provider}/{model}"
            )
        return candidate
    if not eligible:
        raise RuntimeError("No eligible provider/model is configured in this GitHub Actions runner.")
    return eligible[0]


async def _request_arm(client, evaluation_context, provider, model, query, arm):
    import httpx

    state: dict[str, Any] = {
        "retrieved_candidates": [],
        "auxiliary_claim_adjudication": None,
        "base_system_prompt_sha256": None,
        "route_input_system_prompt_sha256": None,
        "user_content_sha256": None,
        "route_operation": None,
        "max_tokens": None,
        "schema_sha256": None,
        "schema_mode": None,
        "provider_timeout_seconds": None,
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
            "auxiliary_claim_adjudication": state["auxiliary_claim_adjudication"],
            "base_system_prompt_sha256": state["base_system_prompt_sha256"],
            "route_input_system_prompt_sha256": state["route_input_system_prompt_sha256"],
            "user_content_sha256": state["user_content_sha256"],
            "route_operation": state["route_operation"],
            "max_tokens": state["max_tokens"],
            "schema_sha256": state["schema_sha256"],
            "schema_mode": state["schema_mode"],
            "provider_timeout_seconds": state["provider_timeout_seconds"],
            "route_source": payload.get("route_source"),
            "deployment_commit_sha": payload.get("deployment_commit_sha"),
        }
    finally:
        CAPTURE_CONTEXT.reset(token)


def _counterbalanced_arm_order(case_index: int) -> tuple[str, str]:
    """Alternate treatment-first and control-first order across adjacent cases."""
    return ("control", "treatment") if case_index % 2 == 0 else ("treatment", "control")


def _skipped_arm(reason: str) -> dict:
    return {
        "http_status": None,
        "transport_error_type": None,
        "ok": False,
        "response": "",
        "request_id": "",
        "provider": "",
        "model": "",
        "llm_invoked": False,
        "response_provenance": {},
        "answer_envelope": None,
        "retrieved_candidates": [],
        "auxiliary_claim_adjudication": None,
        "provider_adjudication": {
            "status": "not_observed",
            "selected_candidate_ids": [],
            "rejection_reason_codes": [],
            "application_evidence_present": False,
            "application_evidence_candidate_ids": [],
            "application": "not_observed",
        },
        "base_system_prompt_sha256": None,
        "route_input_system_prompt_sha256": None,
        "user_content_sha256": None,
        "route_operation": None,
        "max_tokens": None,
        "schema_sha256": None,
        "schema_mode": None,
        "provider_timeout_seconds": None,
        "route_source": None,
        "deployment_commit_sha": None,
        "skipped_reason": reason,
    }


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
    try:
        chosen = _choose_provider_candidate(eligible, args.provider, args.model)
    except RuntimeError as exc:
        if not eligible:
            raise RuntimeError(
                "No eligible provider/model is configured in this GitHub Actions runner. "
                "Configure an approved provider credential as a repository or environment secret."
            ) from exc
        raise
    provider = str(chosen.get("provider") or "").strip()
    model = str(chosen.get("model") or "").strip()
    if not provider or not model:
        raise RuntimeError("Provider bank returned an incomplete provider/model identity.")

    # The matched-pair harness may use a narrowly bounded provider timeout
    # override for the exact pinned lane. This does not change application defaults,
    # production configuration, or the shared request deadline.
    original_provider_call_timeout = provider_bank._provider_call_timeout
    original_quota_guarded_call = provider_bank._quota_guarded_call

    def evaluation_provider_call_timeout(operation, item=None, attempt_index=1):
        timeout = original_provider_call_timeout(operation, item, attempt_index)
        if (
            operation == "general_guide_composition"
            and str((item or {}).get("provider") or "") == provider
            and str((item or {}).get("model") or "") == model
        ):
            effective_timeout = max(float(timeout or 0), float(args.provider_timeout_seconds))
            state = CAPTURE_CONTEXT.get()
            if state is not None:
                state["provider_timeout_seconds"] = effective_timeout
            return effective_timeout
        return timeout

    def evaluation_quota_guarded_call(
        use_core, item, messages, max_tokens, schema=None,
        timeout_override=None, operation=None,
    ):
        effective_operation = operation or provider_bank._PROVIDER_OPERATION_CONTEXT.get()
        if (
            effective_operation == "general_guide_composition"
            and str((item or {}).get("provider") or "") == provider
            and str((item or {}).get("model") or "") == model
        ):
            state = CAPTURE_CONTEXT.get()
            if state is not None:
                state["max_tokens"] = max_tokens
                state["schema_sha256"] = (
                    _sha256(json.dumps(schema, sort_keys=True, separators=(",", ":")))
                    if isinstance(schema, dict) else None
                )
                state["schema_mode"] = schema.get("mode") if isinstance(schema, dict) else None
                state["provider_timeout_seconds"] = timeout_override
        return original_quota_guarded_call(
            use_core, item, messages, max_tokens, schema,
            timeout_override=timeout_override, operation=operation,
        )

    provider_bank._provider_call_timeout = evaluation_provider_call_timeout
    provider_bank._quota_guarded_call = evaluation_quota_guarded_call
    restore_observers = _install_observers(composition, main)
    def restore():
        restore_observers()
        provider_bank._provider_call_timeout = original_provider_call_timeout
        provider_bank._quota_guarded_call = original_quota_guarded_call

    records = []
    blind_cases = []
    unblinding = {}
    try:
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://gold-star-evaluation.local",
            timeout=httpx.Timeout(args.timeout_seconds),
        ) as client:
            provider_lane_available = True
            provider_attempted = False
            for case_index, case in enumerate(cases):
                arms = {}
                call_order = _counterbalanced_arm_order(case_index)
                attempted_arm_order = []
                for arm in call_order:
                    if not provider_lane_available:
                        arms[arm] = _skipped_arm("previous_pinned_provider_attempt_unavailable")
                        continue
                    if provider_attempted and args.inter_call_delay_seconds:
                        await asyncio.sleep(args.inter_call_delay_seconds)
                    attempted_arm_order.append(arm)
                    arms[arm] = await _request_arm(
                        client, evaluation_context, provider, model, case["query"], arm
                    )
                    provider_attempted = True
                    result = arms[arm]
                    if (
                        not result["llm_invoked"]
                        or result["provider"] != provider
                        or result["model"] != model
                        or result["http_status"] != 200
                    ):
                        # A deterministic fallback, 429, timeout, or attribution mismatch
                        # closes this pinned lane. Do not spend more quota on doomed pairs.
                        provider_lane_available = False

                control, treatment = arms["control"], arms["treatment"]
                failures = []
                for arm_name, result in arms.items():
                    if result.get("skipped_reason"):
                        failures.append(f"{arm_name}_skipped_{result['skipped_reason']}")
                    if result["http_status"] != 200 or not result["ok"] or not result["response"].strip():
                        failures.append(f"{arm_name}_visitor_response_invalid")
                    if not result["llm_invoked"]:
                        failures.append(f"{arm_name}_not_attributable_llm")
                    if result["provider"] != provider or result["model"] != model:
                        failures.append(f"{arm_name}_provider_model_pin_mismatch")
                if control["retrieved_candidates"]:
                    failures.append("control_exposed_gold_star_guidance")
                if not control["user_content_sha256"] or not treatment["user_content_sha256"]:
                    failures.append("provider_route_prompt_capture_missing")
                elif control["user_content_sha256"] != treatment["user_content_sha256"]:
                    failures.append("paired_user_content_mismatch")
                if not control["base_system_prompt_sha256"] or not treatment["base_system_prompt_sha256"]:
                    failures.append("provider_route_base_system_prompt_capture_missing")
                elif control["base_system_prompt_sha256"] != treatment["base_system_prompt_sha256"]:
                    failures.append("paired_base_system_prompt_mismatch")
                if not control["route_input_system_prompt_sha256"] or not treatment["route_input_system_prompt_sha256"]:
                    failures.append("provider_route_system_prompt_capture_missing")
                elif control["route_input_system_prompt_sha256"] == treatment["route_input_system_prompt_sha256"]:
                    failures.append("treatment_system_prompt_not_adapted")
                if (
                    control["route_operation"] != treatment["route_operation"]
                    or control["max_tokens"] != treatment["max_tokens"]
                    or control["schema_sha256"] != treatment["schema_sha256"]
                    or control["schema_mode"] != treatment["schema_mode"]
                    or control["provider_timeout_seconds"] != treatment["provider_timeout_seconds"]
                ):
                    failures.append("paired_generation_configuration_mismatch")

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

                case_family = str(
                    case.get("case_family") or case.get("question_type") or case["case_id"]
                )
                # The control system prompt is the actual non-adaptive baseline sent
                # through the same route. Pairing also includes the exact shared user
                # message hash; treatment's adaptive system prompt hash is retained per arm.
                base_prompt_fingerprint = _sha256(
                    "NON_ADAPTIVE_BASE_SYSTEM_PROMPT_SHA256\n"
                    + str(control["base_system_prompt_sha256"] or "")
                    + "\nUSER_CONTENT_SHA256\n"
                    + str(control["user_content_sha256"] or "")
                )
                # Effective Groq payload contract for the exact pinned lane,
                # verified against provider_bank._groq. Schema identity is hashed.
                generation_config = {
                    "operation": control["route_operation"],
                    "max_completion_tokens": control["max_tokens"],
                    "provider": provider,
                    "model": model,
                    "temperature": 0.0,
                    "top_p": "not_supplied_provider_default",
                    "stop": "not_supplied",
                    "presence_penalty": "not_supplied_provider_default",
                    "frequency_penalty": "not_supplied_provider_default",
                    "chat_template_kwargs": "not_supplied",
                    "extra_body": "not_supplied",
                    "response_format": (
                        "omitted_text_mode" if control["schema_mode"] == "text"
                        else "json_schema" if control["schema_sha256"] else "json_object"
                    ),
                    "schema_sha256": control["schema_sha256"],
                    "schema_mode": control["schema_mode"],
                    "reasoning_effort": "low",
                    "include_reasoning": False,
                    "provider_timeout_seconds": control["provider_timeout_seconds"],
                    "provider_sdk_max_retries": (
                        0 if control["provider_timeout_seconds"] is not None else "not_invoked"
                    ),
                    "inter_call_delay_seconds": args.inter_call_delay_seconds,
                    "evaluation_retry_policy": "one exact pinned provider/model; no alternate lane",
                }
                generation_fingerprint = _sha256(
                    json.dumps(generation_config, sort_keys=True, separators=(",", ":"))
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
                    "arm_call_order": list(attempted_arm_order),
                    "arm_evaluation_order": list(call_order),
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
        "evaluation_id": suite["evaluation_id"],
        "evaluation_mode": "local_candidate_same_provider_model_paired_generation",
        "semantic_certification": False,
        "runtime_commit": runtime_commit,
        "provider": provider,
        "model": model,
        "provider_call_spacing_seconds": args.inter_call_delay_seconds,
        "provider_call_timeout_seconds": args.provider_timeout_seconds,
        "arm_order_policy": "counterbalanced_by_case_index_control_first_on_even_treatment_first_on_odd",
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


def _build_evaluation_template(report: dict) -> dict:
    """Create an intentionally incomplete, privacy-safe human scoring template."""
    from gold_star_adaptation_evaluation import HARD_GATE_DIMENSIONS, SCORE_DIMENSIONS

    records = []
    for case in report.get("cases", []):
        critical = list(case.get("critical_dimensions") or [])
        score_dimensions = sorted(set(SCORE_DIMENSIONS) | set(critical))
        shared = {
            "runtime_commit": case["runtime_commit"],
            "composition_contract_version": case["composition_contract_version"],
            "provider": case["provider"],
            "model": case["model"],
            "base_prompt_fingerprint": case["base_prompt_fingerprint"],
            "generation_config_fingerprint": case["generation_config_fingerprint"],
            "gold_star_registry_sha256": case["gold_star_registry_sha256"],
        }
        record = {
            "evaluation_id": f"{report['evaluation_id']}:{case['case_id']}",
            "case_id": case["case_id"],
            "case_family": case["case_family"],
            **shared,
            "blind_review": False,
            "reviewer_verdict": None,
            "reviewer_evidence_ref": f"blind-review-package.json#cases/{case['case_id']}",
            "reviewed_at": None,
            "critical_dimensions": critical,
        }
        for arm_name, enabled in (("control", False), ("treatment", True)):
            record[arm_name] = {
                "adaptation_enabled": enabled,
                "output_artifact_ref": (
                    f"matched-pair-evidence.json#cases/{case['case_id']}/{arm_name}"
                ),
                **shared,
                "scores": {dimension: None for dimension in score_dimensions},
                "na_reasons": {},
                "hard_gates": {dimension: None for dimension in HARD_GATE_DIMENSIONS},
            }
        records.append(record)
    return {
        "schema_version": "1.0",
        "evaluation_id": report["evaluation_id"],
        "status": "awaiting_blind_human_review",
        "instructions": (
            "Score Response A and Response B in the blind review package first. "
            "Only after scoring, consult the separate unblinding key and map scores "
            "to control/treatment here. Set blind_review=true, set reviewer_verdict to "
            "improved, not_improved, regressed, or inconclusive, and provide reviewed_at "
            "as an ISO-8601 timestamp. Complete every score and hard gate. For NA scores, "
            "use only these na_reasons codes: not_relevant_to_question, "
            "no_archive_specific_claim, no_doorway_requested_or_permitted, or "
            "dimension_not_applicable_to_case. Then run "
            "gold_star_adaptation_evaluation.evaluate_batch."
        ),
        "records": records,
    }


def main_cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/gold-star-matched-pairs"))
    parser.add_argument("--timeout-seconds", type=float, default=90.0)
    parser.add_argument(
        "--provider-timeout-seconds", type=float, default=8.0,
        help="Evaluation-only timeout for the exact pinned lane; bounded to 5-10 seconds.",
    )
    parser.add_argument("--provider", default="", help="Optional exact provider pin.")
    parser.add_argument("--model", default="", help="Optional exact model pin.")
    parser.add_argument(
        "--inter-call-delay-seconds", type=float, default=65.0,
        help="Delay between pinned provider calls to respect the 60-second TPM window.",
    )
    args = parser.parse_args()
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be greater than zero.")
    if not 5.0 <= args.provider_timeout_seconds <= 10.0:
        parser.error("--provider-timeout-seconds must be between 5 and 10.")
    if args.inter_call_delay_seconds < 60:
        parser.error("--inter-call-delay-seconds must be at least 60 to respect the provider TPM window.")

    report = asyncio.run(capture(args))
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    blind_cases = report.pop("_blind_review_cases")
    unblinding_key = report.pop("_unblinding_key")
    evaluation_template = _build_evaluation_template(report)
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
            "reviewer_verdicts": [
                {"value": "improved", "guidance": "Treatment is materially better overall than control."},
                {"value": "not_improved", "guidance": "Treatment is not materially better than control."},
                {"value": "regressed", "guidance": "Treatment is materially worse or violates a required boundary."},
                {"value": "inconclusive", "guidance": "The evidence does not support a reliable comparison."},
            ],
            "na_reason_codes": [
                "not_relevant_to_question",
                "no_archive_specific_claim",
                "no_doorway_requested_or_permitted",
                "dimension_not_applicable_to_case",
            ],
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "unblinding-key.json").write_text(
        json.dumps(unblinding_key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "paired-evaluation-template.json").write_text(
        json.dumps(evaluation_template, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
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
