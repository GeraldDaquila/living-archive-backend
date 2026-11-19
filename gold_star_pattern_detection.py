"""Evidence-gated detection of recurring reasoning weaknesses.

This module consumes only consented, de-identified, human-reviewed metadata.
It never accepts visitor query/answer text, never learns from unreviewed traffic,
and never activates or writes a Gold Star. Detection creates candidates only;
registry elevation and runtime activation remain separate governed decisions.
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Mapping

_ALLOWED_FIELDS = frozenset({
    "case_id",
    "evidence_ref",
    "consent_status",
    "deidentified",
    "human_review_status",
    "review_outcome",
    "task_family",
    "domain",
    "reasoning_operation",
    "failed_criterion",
})
_FORBIDDEN_CONTENT_FIELDS = frozenset({
    "query", "question", "answer", "response", "visitor_text",
    "raw_query", "raw_answer", "email", "user_id", "ip_address",
})
_LABEL = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")
_EVIDENCE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{2,127}$")


def _label(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    candidate = value.strip().casefold()
    return candidate if _LABEL.fullmatch(candidate) else ""


def _valid_evidence(item: Any) -> bool:
    if not isinstance(item, Mapping):
        return False
    if set(item) - _ALLOWED_FIELDS:
        return False
    if _FORBIDDEN_CONTENT_FIELDS.intersection(item):
        return False
    if item.get("consent_status") != "CONSENTED":
        return False
    if item.get("deidentified") is not True:
        return False
    if item.get("human_review_status") != "COMPLETE":
        return False
    if item.get("review_outcome") != "CONFIRMED_DEFECT":
        return False
    if not _label(item.get("case_id")):
        return False
    if not _label(item.get("task_family")):
        return False
    if not _label(item.get("domain")):
        return False
    if not _label(item.get("reasoning_operation")):
        return False
    if not _label(item.get("failed_criterion")):
        return False
    ref = item.get("evidence_ref")
    if not isinstance(ref, str) or not _EVIDENCE_REF.fullmatch(ref.strip()):
        return False
    if "://" in ref:
        return False
    return True


def detect_recurring_patterns(
    evidence_records: Iterable[Mapping[str, Any]],
    *,
    min_support: int = 3,
    min_domains: int = 2,
    min_task_families: int = 2,
) -> Dict[str, Any]:
    """Create review-only candidates from qualifying metadata evidence.

    A candidate requires distinct cases, distinct evidence references, multiple
    domains and task families, explicit consent, de-identification, completed
    human review, and a confirmed defect. Raw question/answer content is rejected.
    """
    if min_support < 3 or min_domains < 2 or min_task_families < 2:
        raise ValueError("Pattern detection thresholds may not be weakened below the governed minimum.")

    groups: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    seen_cases = set()
    excluded = 0
    for item in evidence_records:
        if not _valid_evidence(item):
            excluded += 1
            continue
        case_id = str(item["case_id"]).strip()
        if case_id in seen_cases:
            excluded += 1
            continue
        seen_cases.add(case_id)
        operation = _label(item["reasoning_operation"])
        groups[operation].append({
            "case_id": case_id,
            "evidence_ref": str(item["evidence_ref"]).strip(),
            "task_family": _label(item["task_family"]),
            "domain": _label(item["domain"]),
            "failed_criterion": _label(item["failed_criterion"]),
        })

    candidates = []
    for operation, observations in sorted(groups.items()):
        case_ids = sorted({x["case_id"] for x in observations})
        evidence_refs = sorted({x["evidence_ref"] for x in observations})
        domains = sorted({x["domain"] for x in observations})
        task_families = sorted({x["task_family"] for x in observations})
        if (
            len(case_ids) < min_support
            or len(evidence_refs) < min_support
            or len(domains) < min_domains
            or len(task_families) < min_task_families
        ):
            continue
        candidates.append({
            "candidate_id": f"pattern-{operation}",
            "status": "CANDIDATE_REQUIRES_HUMAN_ADJUDICATION",
            "reasoning_operation": operation,
            "support_count": len(case_ids),
            "evidence_case_ids": case_ids,
            "evidence_refs": evidence_refs,
            "domain_coverage": domains,
            "task_family_coverage": task_families,
            "failed_criteria": sorted({x["failed_criterion"] for x in observations}),
            "semantic_certification": False,
            "runtime_eligible": False,
            "lesson_text": None,
            "doorway": None,
            "next_gate": "target_adjacent_unrelated_tests_and_explicit_owner_approval",
        })
    return {
        "schema_version": "1.0",
        "mode": "consented_deidentified_review_metadata_only",
        "candidates": candidates,
        "qualifying_observations": sum(len(x) for x in groups.values()),
        "excluded_observations": excluded,
        "semantic_certification": False,
        "runtime_activation": False,
    }


def adjudicate_pattern_candidate(
    candidate: Mapping[str, Any],
    *,
    decision: str,
    reviewer: str,
    rationale: str,
    target_tests_passed: bool,
    adjacent_tests_passed: bool,
    unrelated_negative_controls_passed: bool,
    explicit_owner_approval: bool = False,
) -> Dict[str, Any]:
    """Record a bounded adjudication without changing registry or runtime state."""
    if candidate.get("status") != "CANDIDATE_REQUIRES_HUMAN_ADJUDICATION":
        raise ValueError("Only an unapproved pattern candidate can be adjudicated.")
    if decision not in {"APPROVE", "REVISE", "REJECT"}:
        raise ValueError("Decision must be APPROVE, REVISE, or REJECT.")
    if not reviewer.strip() or not rationale.strip():
        raise ValueError("Reviewer and rationale are required.")

    if decision == "REJECT":
        status = "REJECTED"
    elif decision == "REVISE":
        status = "REVISION_REQUIRED"
    elif not (
        target_tests_passed
        and adjacent_tests_passed
        and unrelated_negative_controls_passed
        and explicit_owner_approval
    ):
        status = "APPROVAL_BLOCKED"
    else:
        status = "APPROVED_FOR_SEPARATE_REGISTRY_REVIEW_ONLY"

    return {
        "candidate_id": candidate.get("candidate_id"),
        "decision": decision,
        "status": status,
        "reviewer": reviewer.strip(),
        "rationale": rationale.strip(),
        "target_tests_passed": bool(target_tests_passed),
        "adjacent_tests_passed": bool(adjacent_tests_passed),
        "unrelated_negative_controls_passed": bool(unrelated_negative_controls_passed),
        "explicit_owner_approval": bool(explicit_owner_approval),
        "registry_write_performed": False,
        "runtime_activated": False,
        "next_step": (
            "separate_registry_change_with_provenance_freeze_and_numbering_checks"
            if status == "APPROVED_FOR_SEPARATE_REGISTRY_REVIEW_ONLY"
            else "no_runtime_change"
        ),
    }
