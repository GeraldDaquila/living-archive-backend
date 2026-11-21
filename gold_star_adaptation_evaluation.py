"""Governed paired evaluation for Gold Star structural adaptation.

This module evaluates whether reviewed Gold Star guidance improves answers on
held-out benchmark cases. It is deliberately offline and non-mutating: it does
not collect visitor content, select lessons at runtime, or promote registry
records. Passing the gate means evidence is ready for human promotion review,
not that a lesson is automatically approved.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from math import ceil
from typing import Any

VERSION = "1.0"
SCORE_DIMENSIONS = (
    "question_fit",
    "substantive_resolution",
    "reasoning_coherence",
    "evidence_integrity",
    "epistemic_calibration",
    "practical_utility",
)
HARD_GATE_DIMENSIONS = (
    "evidence_integrity",
    "epistemic_calibration",
    "safety",
)
VERDICTS = frozenset({"improved", "not_improved", "regressed", "inconclusive"})
FORBIDDEN_KEYS = frozenset({
    "question", "query", "answer", "response", "user_id", "session_id",
    "email", "phone", "content_hash", "visitor_id",
})
MIN_PAIRED_CASES = 3
MIN_CASE_FAMILIES = 2
MIN_MEAN_SCORE_DELTA = 0.5
MIN_IMPROVED_SHARE = 2 / 3


def _contains_forbidden_content(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key).casefold() in FORBIDDEN_KEYS
            or _contains_forbidden_content(item)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_forbidden_content(item) for item in value)
    return False


def _valid_scores(value: Any) -> bool:
    return (
        isinstance(value, Mapping)
        and set(value) == set(SCORE_DIMENSIONS)
        and all(type(value[key]) is int and 1 <= value[key] <= 5 for key in SCORE_DIMENSIONS)
    )


def _valid_gates(value: Any) -> bool:
    return (
        isinstance(value, Mapping)
        and set(value) == set(HARD_GATE_DIMENSIONS)
        and all(
            isinstance(value[key], str) and value[key] in {"pass", "fail"}
            for key in HARD_GATE_DIMENSIONS
        )
    )


def _mean_score(scores: Mapping[str, int]) -> float:
    return sum(scores[key] for key in SCORE_DIMENSIONS) / len(SCORE_DIMENSIONS)


def evaluate_paired_case(record: Any) -> dict[str, Any]:
    """Validate one blind control/treatment pair and report evidence, not approval."""
    if not isinstance(record, Mapping):
        return {"valid": False, "status": "invalid", "reason": "not_object"}
    if _contains_forbidden_content(record):
        return {"valid": False, "status": "invalid", "reason": "content_or_identity_field_prohibited"}

    required = {
        "evaluation_id", "case_id", "case_family", "runtime_commit",
        "composition_contract_version", "provider", "model", "blind_review",
        "reviewer_verdict", "reviewer_evidence_ref", "reviewed_at",
        "control", "treatment",
    }
    missing = sorted(required - set(record))
    if missing:
        return {"valid": False, "status": "invalid", "reason": "missing_fields", "missing": missing}

    for key in ("evaluation_id", "case_id", "case_family", "runtime_commit",
                "composition_contract_version", "provider", "model",
                "reviewer_evidence_ref", "reviewed_at"):
        if not isinstance(record.get(key), str) or not record[key].strip():
            return {"valid": False, "status": "invalid", "reason": f"invalid_{key}"}

    if record.get("blind_review") is not True:
        return {"valid": False, "status": "invalid", "reason": "review_not_blind"}
    if record.get("reviewer_verdict") not in VERDICTS:
        return {"valid": False, "status": "invalid", "reason": "invalid_reviewer_verdict"}
    try:
        datetime.fromisoformat(str(record["reviewed_at"]).replace("Z", "+00:00"))
    except ValueError:
        return {"valid": False, "status": "invalid", "reason": "invalid_reviewed_at"}

    arms = {}
    for name, expected_enabled in (("control", False), ("treatment", True)):
        arm = record.get(name)
        if not isinstance(arm, Mapping):
            return {"valid": False, "status": "invalid", "reason": f"invalid_{name}_arm"}
        if arm.get("adaptation_enabled") is not expected_enabled:
            return {"valid": False, "status": "invalid", "reason": f"invalid_{name}_condition"}
        if not isinstance(arm.get("output_artifact_ref"), str) or not arm["output_artifact_ref"].strip():
            return {"valid": False, "status": "invalid", "reason": f"missing_{name}_artifact"}
        if not _valid_scores(arm.get("scores")):
            return {"valid": False, "status": "invalid", "reason": f"invalid_{name}_scores"}
        if not _valid_gates(arm.get("hard_gates")):
            return {"valid": False, "status": "invalid", "reason": f"invalid_{name}_hard_gates"}
        arms[name] = arm

    if arms["control"]["output_artifact_ref"] == arms["treatment"]["output_artifact_ref"]:
        return {"valid": False, "status": "invalid", "reason": "paired_outputs_not_distinct"}

    # Keep the comparison paired: only the adaptive-guidance condition may differ.
    for key in ("provider", "model", "runtime_commit", "composition_contract_version"):
        for arm_name in ("control", "treatment"):
            arm_value = arms[arm_name].get(key)
            if not isinstance(arm_value, str) or arm_value != record[key]:
                return {"valid": False, "status": "invalid", "reason": f"unpaired_{key}"}

    baseline = _mean_score(arms["control"]["scores"])
    treatment = _mean_score(arms["treatment"]["scores"])
    delta = round(treatment - baseline, 4)
    treatment_hard_gate_failures = [
        dimension for dimension in HARD_GATE_DIMENSIONS
        if arms["treatment"]["hard_gates"][dimension] == "fail"
    ]
    regressions = [
        dimension for dimension in HARD_GATE_DIMENSIONS
        if arms["control"]["hard_gates"][dimension] == "pass"
        and arms["treatment"]["hard_gates"][dimension] == "fail"
    ]
    verdict = record["reviewer_verdict"]
    if treatment_hard_gate_failures or verdict == "regressed":
        status = "reviewed_regression"
    elif verdict == "improved" and delta > 0 and not regressions:
        status = "reviewed_improvement"
    elif verdict == "inconclusive":
        status = "review_required"
    else:
        status = "reviewed_no_improvement"

    return {
        "valid": True,
        "status": status,
        "evaluation_id": record["evaluation_id"],
        "case_id": record["case_id"],
        "case_family": record["case_family"],
        "mean_score_delta": delta,
        "hard_gate_regressions": regressions,
        "treatment_hard_gate_failures": treatment_hard_gate_failures,
        "reviewer_verdict": verdict,
        "human_reviewed": True,
    }


def evaluate_batch(records: Any) -> dict[str, Any]:
    """Assess whether paired evidence is sufficient to request human promotion review.

    This function never mutates the Gold Star registry. It requires multiple
    held-out cases, cross-family coverage, blind human review, positive measured
    movement, and zero hard-gate regressions before returning an eligible state.
    """
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        return {"valid": False, "status": "invalid", "reason": "records_not_sequence"}
    evaluated = [evaluate_paired_case(record) for record in records]
    invalid = [item for item in evaluated if not item.get("valid")]
    if invalid:
        return {
            "valid": False,
            "status": "invalid",
            "reason": "one_or_more_invalid_pairs",
            "invalid_count": len(invalid),
            "cases": evaluated,
        }
    count = len(evaluated)
    case_ids = [item["case_id"] for item in evaluated]
    evaluation_ids = [item["evaluation_id"] for item in evaluated]
    if len(set(case_ids)) != count or len(set(evaluation_ids)) != count:
        return {
            "valid": False,
            "status": "invalid",
            "reason": "duplicate_case_or_evaluation_id",
            "cases": evaluated,
        }
    families = {item["case_family"] for item in evaluated}
    mean_delta = round(sum(item["mean_score_delta"] for item in evaluated) / count, 4) if count else 0.0
    improved = sum(item["reviewer_verdict"] == "improved" for item in evaluated)
    regressions = sum(
        bool(item["treatment_hard_gate_failures"])
        or bool(item["hard_gate_regressions"])
        or item["status"] == "reviewed_regression"
        for item in evaluated
    )
    reasons = []
    if count < MIN_PAIRED_CASES:
        reasons.append("insufficient_paired_cases")
    if len(families) < MIN_CASE_FAMILIES:
        reasons.append("insufficient_case_family_coverage")
    if mean_delta < MIN_MEAN_SCORE_DELTA:
        reasons.append("mean_improvement_below_threshold")
    if improved < ceil(count * MIN_IMPROVED_SHARE):
        reasons.append("insufficient_human_reviewed_improvements")
    if regressions:
        reasons.append("hard_gate_or_reviewed_regression")

    return {
        "valid": True,
        "status": "eligible_for_human_promotion_review" if not reasons else "evidence_insufficient",
        "policy_version": VERSION,
        "paired_case_count": count,
        "case_family_count": len(families),
        "mean_score_delta": mean_delta,
        "human_reviewed_improvement_count": improved,
        "regression_count": regressions,
        "reasons": reasons,
        "registry_mutated": False,
        "human_promotion_approval_required": True,
        "cases": evaluated,
    }
