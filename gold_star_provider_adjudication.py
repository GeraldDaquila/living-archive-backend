"""Bounded provider-reported Gold Star adjudication contract.

The provider may report a candidate decision and an exact answer span. The
runtime independently validates candidate membership, complete disposition,
reason codes, discipline provenance, and exact span presence. This is evidence
of a structured provider report, not proof of semantic application or quality.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any
import re

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
        "application_evidence_reason": "not_observed",
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
    # Require one bounded evidence entry for every disposition. Selected
    # candidates must point to an exact answer substring; rejected candidates
    # must carry an empty span. This makes omission detectable without making
    # reject-all invalid or retaining visitor content in telemetry.
    spans = value.get("application_evidence_spans")
    evidence_ids: list[str] = []
    evidence_reason = "span_entry_count_mismatch"
    spans_valid = isinstance(spans, list) and len(spans) == len(index)
    span_by_id: dict[str, str] = {}
    if spans_valid:
        for item in spans:
            if not isinstance(item, Mapping) or set(item) != {"candidate_id", "span"}:
                spans_valid = False
                evidence_reason = "invalid_span_entry"
                break
            candidate_id, span = item.get("candidate_id"), item.get("span")
            if (
                not isinstance(candidate_id, str)
                or candidate_id not in index
                or candidate_id in span_by_id
            ):
                spans_valid = False
                evidence_reason = "invalid_span_candidate_id"
                break
            if not isinstance(span, str) or len(span) > MAX_EVIDENCE_SPAN:
                spans_valid = False
                evidence_reason = "invalid_span_length"
                break
            span_by_id[candidate_id] = span
        if spans_valid and set(span_by_id) != set(index):
            spans_valid = False
            evidence_reason = "span_candidate_coverage_incomplete"
    if spans_valid:
        normalized_response = re.sub(r"\\s+", " ", str(response or "")).strip().casefold()
        for candidate_id in selected:
            span = re.sub(r"\\s+", " ", span_by_id.get(candidate_id, "")).strip().casefold()
            if not 12 <= len(span) <= MAX_EVIDENCE_SPAN:
                spans_valid = False
                evidence_reason = "selected_span_missing_or_out_of_bounds"
                break
            if span not in normalized_response:
                spans_valid = False
                evidence_reason = "selected_span_not_in_final_response"
                break
            evidence_ids.append(candidate_id)
        if spans_valid and any(
            span_by_id.get(candidate_id) != ""
            for candidate_id in set(index) - set(selected)
        ):
            spans_valid = False
            evidence_reason = "rejected_span_not_empty"
    if not spans_valid:
        evidence_ids = []
    elif selected:
        evidence_reason = "exact_selected_spans_validated"
    else:
        evidence_reason = "no_selected_candidates"
    span_present = bool(selected) and set(evidence_ids) == set(selected)
    return {
        "status": "provider_reported_selected" if selected else "provider_reported_rejected_all",
        "selected_candidate_ids": selected,
        "rejection_reason_codes": rejected,
        "reasoning_discipline_ids": sorted(disciplines),
        "application_evidence_present": span_present,
        "application_evidence_candidate_ids": evidence_ids,
        "application": "provider_asserted_span_present" if span_present else "not_observed",
        "application_evidence_reason": evidence_reason,
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
        " for reject). Assess activation scope and abstention boundary; accept semantically equivalent "
        "questions. Select only distinct, relevant candidates. After drafting the final response, emit one "
        "span object per candidate ID: selected IDs get an exact 12–240 character contiguous sentence or "
        "clause from the answer showing their distinctive reasoning operation (an exact substring); rejected "
        "IDs get an empty string. Never select without a span; reject-all uses empty spans. "
        "No hidden reasoning or chain-of-thought. "
        "This report is not visitor-facing and is not proof of semantic quality; "
        "the runtime validates IDs, complete disposition, reason codes, and exact "
        "span presence. Improvement still requires paired evaluation. "
        "Output one object, not adjudication alone: "
        '{"response":"complete visitor answer","doorway_title":"title or empty",'
        '"response_shape":"shape","adaptive_adjudication":'
        '{"candidate_assessments":[...],"application_evidence_spans":[...]}}.'
    )
