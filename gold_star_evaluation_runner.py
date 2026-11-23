"""Synthetic-only, non-persistent Gold Star matched-pair generation.

This runner accepts a fixed held-out case identifier, never visitor-supplied
question text. It returns blinded output artifacts and a separate operator
manifest; it does not persist either output or evaluation records.
"""
from __future__ import annotations

import hashlib
import json
import secrets
import time
import uuid
from pathlib import Path
from typing import Any

import general_guide_composition as _composition
from gold_star_evaluation_context import evaluation_context


HELD_OUT_CASE_IDS = frozenset({
    "heldout-water-boiling-point-001",
    "heldout-cosmology-life-001",
    "heldout-practical-trust-001",
    "heldout-strategic-governance-001",
    "heldout-technical-verification-001",
    "heldout-uncertain-causation-001",
    "heldout-explicit-no-handoff-001",
})
ARM_TIMEOUT_SECONDS = 45
MAX_PAIRS_PER_PROCESS = 3
MIRROR_SERVICE_ID = "srv-db2s2bid0e5s73e7gt9g"


class GoldStarEvaluationRunError(ValueError):
    """Safe, content-free evaluation failure with a stable reason code."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def evaluation_route_authorized(
    *,
    service_id: str,
    enabled_flag: str,
    expected_secret: str,
    supplied_secret: str,
) -> bool:
    """Require explicit enablement, the exact Mirror service, and a strong secret."""
    expected = str(expected_secret or "")
    supplied = str(supplied_secret or "")
    if (
        str(service_id or "").strip() != MIRROR_SERVICE_ID
        or str(enabled_flag or "").strip().casefold() != "true"
        or len(expected) < 32
        or not supplied
    ):
        return False
    return secrets.compare_digest(expected, supplied)


def validate_evaluation_request_payload(payload: Any) -> dict[str, str]:
    """Accept only one allowlisted synthetic case and an exact provider/model pin."""
    if not isinstance(payload, dict) or set(payload) != {"case_id", "provider", "model"}:
        raise GoldStarEvaluationRunError("invalid_evaluation_payload")
    case_id = payload.get("case_id")
    provider = payload.get("provider")
    model = payload.get("model")
    if not all(isinstance(value, str) for value in (case_id, provider, model)):
        raise GoldStarEvaluationRunError("invalid_evaluation_payload")
    case_id = case_id.strip()
    provider = provider.strip()
    model = model.strip()
    if (
        case_id not in HELD_OUT_CASE_IDS
        or not provider
        or len(provider) > 128
        or not model
        or len(model) > 256
    ):
        raise GoldStarEvaluationRunError("invalid_evaluation_payload")
    return {"case_id": case_id, "provider": provider, "model": model}


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_held_out_case(case_id: str) -> dict[str, Any]:
    if case_id not in HELD_OUT_CASE_IDS:
        raise GoldStarEvaluationRunError("case_not_allowlisted")
    dataset_path = (
        Path(__file__).resolve().parent
        / "docs"
        / "qa"
        / "guide_learning_evaluation_set.json"
    )
    try:
        dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    except Exception:
        raise GoldStarEvaluationRunError("synthetic_case_dataset_unavailable") from None
    cases = dataset.get("cases") if isinstance(dataset, dict) else None
    if not isinstance(cases, list):
        raise GoldStarEvaluationRunError("synthetic_case_dataset_invalid")
    case = next(
        (
            item for item in cases
            if isinstance(item, dict)
            and item.get("case_id") == case_id
            and item.get("split") == "held_out"
        ),
        None,
    )
    if (
        not isinstance(case, dict)
        or not isinstance(case.get("query"), str)
        or not case["query"].strip()
        or not isinstance(case.get("question_type"), str)
    ):
        raise GoldStarEvaluationRunError("held_out_case_invalid")
    return case


def _generation_config_fingerprint(provider: str, model: str) -> str:
    material = {
        "fingerprint_version": _composition.GOLD_STAR_EVALUATION_GENERATION_CONFIG_VERSION,
        "provider": provider,
        "model": model,
        "operation": _composition.OPERATION,
        "provider_bank_contract_version": _composition.PROVIDER_BANK_CONTRACT_VERSION,
        "max_tokens": 900,
        "schema": None,
        "temperature": 0.0,
        "top_p": None,
        "frequency_penalty": None,
        "presence_penalty": None,
        "routing": "exact-provider-model-local-only",
        "max_provider_attempts": 1,
        "active_active_delegation": False,
        "provider_model_fallback": False,
        "cache": "read-and-write-bypass",
        "arm_timeout_seconds": ARM_TIMEOUT_SECONDS,
    }
    return _sha256(
        json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def _run_arm(
    *,
    case: dict[str, Any],
    arm: str,
    provider: str,
    model: str,
    use_core: Any,
) -> dict[str, Any]:
    try:
        with evaluation_context(arm=arm, provider=provider, model=model):
            result = _composition.compose(
                use_core=use_core,
                query=case["query"],
                context_data={},
                history_text="",
                deadline_monotonic=time.monotonic() + ARM_TIMEOUT_SECONDS,
            )
    except Exception:
        raise GoldStarEvaluationRunError("provider_execution_failed") from None

    if not isinstance(result, dict):
        raise GoldStarEvaluationRunError("provider_candidate_unavailable")
    if result.get("provider") != provider or result.get("model") != model:
        raise GoldStarEvaluationRunError("provider_model_pin_mismatch")
    output = result.get("response")
    if not isinstance(output, str) or not output.strip():
        raise GoldStarEvaluationRunError("provider_output_missing")
    if result.get("_gold_star_evaluation_response_unchanged") is not True:
        raise GoldStarEvaluationRunError("deterministic_rewrite_or_unverified_output")
    base_prompt_fingerprint = str(
        result.get("_gold_star_evaluation_base_prompt_fingerprint") or ""
    )
    if (
        len(base_prompt_fingerprint) != 64
        or any(ch not in "0123456789abcdef" for ch in base_prompt_fingerprint)
    ):
        raise GoldStarEvaluationRunError("base_prompt_fingerprint_missing")

    trace = result.get("_gold_star_adjudication_trace")
    if not isinstance(trace, dict) or trace.get("composition") != "provider_candidate_returned":
        raise GoldStarEvaluationRunError("fresh_provider_composition_unverified")
    if arm == "control":
        if trace.get("candidate_count") != 0:
            raise GoldStarEvaluationRunError("control_arm_received_gold_star_guidance")
    else:
        if (
            type(trace.get("candidate_count")) is not int
            or trace["candidate_count"] < 1
            or trace.get("guidance_exposure") != "included_in_provider_prompt"
        ):
            raise GoldStarEvaluationRunError("treatment_guidance_not_exposed")

    return {
        "output": output.strip(),
        "doorway_title": str(result.get("doorway_title") or ""),
        "doorway_url": str(result.get("doorway_url") or ""),
        "candidate_count": trace["candidate_count"],
        "candidate_ids": list(trace.get("candidate_ids") or []),
        "base_prompt_fingerprint": base_prompt_fingerprint,
        "guidance_exposure": trace.get("guidance_exposure", "not_observed"),
        "composition": trace["composition"],
    }


def run_synthetic_matched_pair(
    *,
    case_id: str,
    provider: str,
    model: str,
    runtime_commit: str,
    registry_sha256: str,
    use_core: Any,
) -> dict[str, Any]:
    """Generate one fresh control/treatment pair for one fixed synthetic case."""
    provider = str(provider or "").strip()
    model = str(model or "").strip()
    runtime_commit = str(runtime_commit or "").strip()
    registry_sha256 = str(registry_sha256 or "").strip().lower()
    if not provider or len(provider) > 128 or not model or len(model) > 256:
        raise GoldStarEvaluationRunError("invalid_provider_model_pin")
    if not runtime_commit:
        raise GoldStarEvaluationRunError("runtime_commit_unavailable")
    if len(registry_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in registry_sha256):
        raise GoldStarEvaluationRunError("registry_digest_invalid")

    case_id = str(case_id or "").strip()
    case = _load_held_out_case(case_id)
    evaluation_id = uuid.uuid4().hex
    # Randomize execution order as well as reviewer presentation order to
    # reduce systematic provider/order effects within each matched pair.
    generation_order = ["control", "treatment"]
    secrets.SystemRandom().shuffle(generation_order)
    arm_results: dict[str, dict[str, Any]] = {}
    for arm in generation_order:
        arm_results[arm] = _run_arm(
            case=case, arm=arm, provider=provider, model=model, use_core=use_core
        )
    control = arm_results["control"]
    treatment = arm_results["treatment"]
    if control["base_prompt_fingerprint"] != treatment["base_prompt_fingerprint"]:
        raise GoldStarEvaluationRunError("base_prompt_fingerprint_mismatch")

    # Artifact references are deliberately arm-neutral; only the private
    # operator manifest retains the control/treatment mapping.
    control_ref = f"urn:gold-star-evaluation:{evaluation_id}:{secrets.token_hex(12)}"
    treatment_ref = f"urn:gold-star-evaluation:{evaluation_id}:{secrets.token_hex(12)}"
    base_fingerprint = control["base_prompt_fingerprint"]
    generation_fingerprint = _generation_config_fingerprint(provider, model)
    contract_version = _composition.CONTRACT_VERSION

    manifest = {
        "evaluation_id": evaluation_id,
        "case_id": case_id,
        "case_family": case["question_type"],
        "runtime_commit": runtime_commit,
        "composition_contract_version": contract_version,
        "provider": provider,
        "model": model,
        "base_prompt_fingerprint": base_fingerprint,
        "generation_config_fingerprint": generation_fingerprint,
        "gold_star_registry_sha256": registry_sha256,
        "critical_dimensions": list(case.get("critical_dimensions") or []),
        "adaptation_scope": "approved_cross_question_structural_guidance_only",
        "control": {
            "adaptation_enabled": False,
            "output_artifact_ref": control_ref,
            "provider": provider,
            "model": model,
            "runtime_commit": runtime_commit,
            "composition_contract_version": contract_version,
            "base_prompt_fingerprint": base_fingerprint,
            "generation_config_fingerprint": generation_fingerprint,
            "gold_star_registry_sha256": registry_sha256,
            "doorway_title": control["doorway_title"],
            "doorway_url": control["doorway_url"],
        },
        "treatment": {
            "adaptation_enabled": True,
            "output_artifact_ref": treatment_ref,
            "provider": provider,
            "model": model,
            "runtime_commit": runtime_commit,
            "composition_contract_version": contract_version,
            "base_prompt_fingerprint": base_fingerprint,
            "generation_config_fingerprint": generation_fingerprint,
            "gold_star_registry_sha256": registry_sha256,
            "doorway_title": treatment["doorway_title"],
            "doorway_url": treatment["doorway_url"],
        },
        "treatment_guidance_candidate_count": treatment["candidate_count"],
        "treatment_guidance_candidate_ids": treatment["candidate_ids"],
        "treatment_guidance_exposure": treatment["guidance_exposure"],
        "control_guidance_candidate_count": control["candidate_count"],
        "control_guidance_exposure": control["guidance_exposure"],
        "review_state": "pending_blind_human_review",
    }

    blind_artifacts = [
        {
            "case_id": case_id,
            "artifact_ref": control_ref,
            "output": control["output"],
        },
        {
            "case_id": case_id,
            "artifact_ref": treatment_ref,
            "output": treatment["output"],
        },
    ]
    secrets.SystemRandom().shuffle(blind_artifacts)

    return {
        "ok": True,
        "status": "ready_for_blind_human_review",
        "persisted": False,
        "visitor_data_used": False,
        "fresh_provider_generations": 2,
        "blind_artifacts": blind_artifacts,
        "operator_manifest": manifest,
    }
