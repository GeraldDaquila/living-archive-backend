"""Bounded provider-reported Gold Star adjudication contract.

The provider may report a candidate decision and an exact answer span. The
runtime independently validates candidate membership, complete disposition,
reason codes, discipline provenance, and exact span presence. This is evidence
of a structured provider report, not proof of semantic application or quality.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

MAX_CANDIDATES = 4
MAX_EVIDENCE_SPAN = 240
REASON_CODES = frozenset({
    "subject_mismatch",
    "lexical_overlap_only",
    "redundant_contribution",
    "boundary_mismatch",
    "conflicting_discipline",
    "insufficient_relevance",
    "no_distinct_contribution",
})
_DECISIONS = frozenset({"select", "reject"})


def _candidate_index(candidates: Any) -> dict[str, Mapping[str, Any]]:
    if not isinstance(candidates, Sequence) or isinstance(candidates, (str, bytes)):
        return {}
    result: dict[str, Mapping[str, Any]] = {}
    for item in list(candidates)[:MAX_CANDIDATES]:
        if not isinstance(item, Mapping):
            continue
        candidate_id = str(item.get("benchmark_id") or "").strip()
        family = str(item.get("reasoning_family") or "").strip()
        if candidate_id and family and candidate_id not in result:
            result[candidate_id] = item
    return result


def normalize_provider_adjudication(
    value: Any, *, response: str, candidates: Any
) -> dict[str, Any]:
    """Validate a provider report without treating it as semantic proof."""
    base = {
        "status": "not_observed",
        "selected_candidate_ids": [],
        "rejection_reason_codes": [],
        "reasoning_discipline_ids": [],
        "application_evidence_present": False,
        "application_evidence_candidate_ids": [],
        "application": "not_observed",
    }
    index = _candidate_index(candidates)
    if not index or not isinstance(value, Mapping):
        return base

    allowed = {"candidate_assessments", "application_evidence_spans"}
    if set(value) != allowed:
        return base
    assessments = value.get("candidate_assessments")
    if not isinstance(assessments, list) or len(assessments) != len(index):
        return base

    seen: set[str] = set()
    selected: list[str] = []
    rejected: list[dict[str, str]] = []
    disciplines: set[str] = set()
    for assessment in assessments:
        if not isinstance(assessment, Mapping) or set(assessment) != {
            "candidate_id", "decision", "reason_code"
        }:
            return base
        candidate_id = assessment.get("candidate_id")
        decision = assessment.get("decision")
        reason = assessment.get("reason_code")
        if (
            not isinstance(candidate_id, str)
            or candidate_id not in index
            or candidate_id in seen
            or decision not in _DECISIONS
        ):
            return base
        seen.add(candidate_id)
        if decision == "select":
            if reason not in (None, ""):
                return base
            selected.append(candidate_id)
            disciplines.add(str(index[candidate_id].get("reasoning_family") or ""))
        else:
            if not isinstance(reason, str) or reason not in REASON_CODES:
                return base
            rejected.append({"candidate_id": candidate_id, "reason_code": reason})

    if seen != set(index):
        return base
    # Selection and application evidence are separate evidence stages. A
    # malformed, missing, or non-matching span must not erase a structurally
    # valid candidate disposition; it simply earns no application credit.
    spans = value.get("application_evidence_spans")
    evidence_ids: list[str] = []
    if not selected:
        if spans not in (None, []):
            return base
    else:
        spans_valid = isinstance(spans, list) and len(spans) == len(selected)
        if spans_valid:
            for item in spans:
                if not isinstance(item, Mapping) or set(item) != {"candidate_id", "span"}:
                    spans_valid = False
                    break
                candidate_id, span = item.get("candidate_id"), item.get("span")
                if (
                    not isinstance(candidate_id, str)
                    or candidate_id not in selected
                    or candidate_id in evidence_ids
                    or not isinstance(span, str)
                    or not 12 <= len(span.strip()) <= MAX_EVIDENCE_SPAN
                    or span.strip() not in str(response or "")
                ):
                    spans_valid = False
                    break
                evidence_ids.append(candidate_id)
            if spans_valid and set(evidence_ids) != set(selected):
                spans_valid = False
        if not spans_valid:
            evidence_ids = []
    span_present = bool(selected) and set(evidence_ids) == set(selected)
    return {
        "status": "provider_reported_selected" if selected else "provider_reported_rejected_all",
        "selected_candidate_ids": selected,
        "rejection_reason_codes": rejected,
        "reasoning_discipline_ids": sorted(disciplines),
        "application_evidence_present": span_present,
        "application_evidence_candidate_ids": evidence_ids,
        "application": "provider_asserted_span_present" if span_present else "not_observed",
    }


def build_adjudication_output_contract(candidates: Any) -> str:
    """Describe the minimal bounded JSON report expected from the provider."""
    index = _candidate_index(candidates)
    if not index:
        return ""
    ids = ", ".join(sorted(index))
    reasons = ", ".join(sorted(REASON_CODES))
    # Keep this contract compact: it is repeated in every provider prompt and
    # competes with visitor evidence for finite context/token budgets.
    return (
        "Add JSON property adaptive_adjudication with exactly two keys: "
        "candidate_assessments and application_evidence_spans. For every candidate "
        "ID (" + ids + "), emit exactly one assessment object with candidate_id, "
        "decision (select/reject), and reason_code (empty string for select; one of " + reasons +
        " for reject). Select only a distinct, materially relevant discipline whose "
        "abstention boundary fits; otherwise reject. For each selected ID, include "
        "one application_evidence_spans object with candidate_id and an exact "
        "contiguous 12–240 character span from response showing its contribution; "
        "use [] when none is selected. No hidden reasoning or chain-of-thought. "
        "This report is not visitor-facing and is not proof of semantic quality; "
        "the runtime validates IDs, complete disposition, reason codes, and exact "
        "span presence. Improvement still requires paired evaluation. "
        "Output one object, not adjudication alone: "
        '{"response":"complete visitor answer","doorway_title":"title or empty",'
        '"response_shape":"shape","adaptive_adjudication":'
        '{"candidate_assessments":[...],"application_evidence_spans":[...]}}.'
    )
