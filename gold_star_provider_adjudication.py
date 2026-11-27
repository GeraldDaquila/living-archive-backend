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
MIN_EVIDENCE_SPAN = 12
MAX_EVIDENCE_SPAN = 120
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
    """Validate provider-reported decisions and exact answer evidence, not semantic proof."""
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
    allowed = {"candidate_assessments", "application_evidence_quotes"}
    legacy_allowed = {"candidate_assessments", "application_evidence_spans"}
    if set(value) not in (allowed, legacy_allowed):
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

    # Prefer exact quoted substrings over model-counted offsets. Models are
    # unreliable at counting Unicode code points in a completed answer; a
    # verbatim quote lets the runtime locate and validate the evidence itself.
    evidence_ids: list[str] = []
    evidence_reason = "evidence_entry_count_mismatch"
    quotes = value.get("application_evidence_quotes")
    if isinstance(quotes, list):
        quotes_by_id: dict[str, str] = {}
        quotes_valid = len(quotes) == len(index)
        if quotes_valid:
            for item in quotes:
                if not isinstance(item, Mapping) or set(item) != {"candidate_id", "quote"}:
                    quotes_valid = False
                    evidence_reason = "invalid_quote_entry"
                    break
                candidate_id, quote = item.get("candidate_id"), item.get("quote")
                if (
                    not isinstance(candidate_id, str)
                    or candidate_id not in index
                    or candidate_id in quotes_by_id
                    or not isinstance(quote, str)
                ):
                    quotes_valid = False
                    evidence_reason = "invalid_quote_candidate_or_value"
                    break
                quotes_by_id[candidate_id] = quote
            if quotes_valid and set(quotes_by_id) != set(index):
                quotes_valid = False
                evidence_reason = "quote_candidate_coverage_incomplete"
        selected_quote_failures: list[str] = []
        if quotes_valid:
            answer = str(response or "")
            for candidate_id in selected:
                quote = quotes_by_id[candidate_id]
                if not MIN_EVIDENCE_SPAN <= len(quote) <= MAX_EVIDENCE_SPAN:
                    selected_quote_failures.append("selected_quote_length_out_of_bounds")
                    continue
                if not quote.strip() or answer.count(quote) != 1:
                    selected_quote_failures.append("selected_quote_not_unique_exact_substring")
                    continue
                evidence_ids.append(candidate_id)
            if any(quotes_by_id[candidate_id] != "" for candidate_id in set(index) - set(selected)):
                quotes_valid = False
                evidence_reason = "rejected_candidate_quote_not_empty"
        if not quotes_valid:
            evidence_ids = []
        elif selected and evidence_ids:
            evidence_reason = (
                "exact_selected_quotes_validated"
                if len(evidence_ids) == len(selected)
                else "partial_selected_quotes_validated"
            )
        elif selected:
            evidence_reason = selected_quote_failures[0] if selected_quote_failures else "selected_quote_not_validated"
        else:
            evidence_reason = "no_selected_candidates"
    else:
        # Backward-compatible validation for responses produced under the
        # earlier offset contract. Never infer or repair an invalid span.
        offsets = value.get("application_evidence_spans")
        evidence_reason = "offset_entry_count_mismatch"
        offsets_valid = isinstance(offsets, list) and len(offsets) == len(index)
        offsets_by_id: dict[str, tuple[int, int]] = {}
        if offsets_valid:
            for item in offsets:
                if not isinstance(item, Mapping) or set(item) != {"candidate_id", "start", "end"}:
                    offsets_valid = False
                    evidence_reason = "invalid_offset_entry"
                    break
                candidate_id, offset_start, offset_end = (
                    item.get("candidate_id"), item.get("start"), item.get("end")
                )
                if (
                    not isinstance(candidate_id, str)
                    or candidate_id not in index
                    or candidate_id in offsets_by_id
                ):
                    offsets_valid = False
                    evidence_reason = "invalid_offset_candidate_id"
                    break
                if (
                    not isinstance(offset_start, int) or isinstance(offset_start, bool)
                    or not isinstance(offset_end, int) or isinstance(offset_end, bool)
                    or offset_start < 0 or offset_end < offset_start
                ):
                    offsets_valid = False
                    evidence_reason = "invalid_offset_bounds"
                    break
                offsets_by_id[candidate_id] = (offset_start, offset_end)
            if offsets_valid and set(offsets_by_id) != set(index):
                offsets_valid = False
                evidence_reason = "offset_candidate_coverage_incomplete"
        selected_offset_failures: list[str] = []
        if offsets_valid:
            answer = str(response or "")
            for candidate_id in selected:
                offset_start, offset_end = offsets_by_id[candidate_id]
                span_length = offset_end - offset_start
                if not MIN_EVIDENCE_SPAN <= span_length <= MAX_EVIDENCE_SPAN:
                    selected_offset_failures.append("selected_offset_span_missing_or_out_of_bounds")
                    continue
                if offset_end > len(answer):
                    selected_offset_failures.append("selected_offset_outside_final_response")
                    continue
                if not answer[offset_start:offset_end].strip():
                    selected_offset_failures.append("selected_offset_span_empty")
                    continue
                evidence_ids.append(candidate_id)
            if any(
                offsets_by_id.get(candidate_id) != (0, 0)
                for candidate_id in set(index) - set(selected)
            ):
                offsets_valid = False
                evidence_reason = "rejected_offset_not_empty"
        if not offsets_valid:
            evidence_ids = []
        elif selected and evidence_ids:
            evidence_reason = (
                "exact_selected_offsets_validated"
                if len(evidence_ids) == len(selected)
                else "partial_selected_offsets_validated"
            )
        elif selected:
            evidence_reason = (
                selected_offset_failures[0]
                if selected_offset_failures
                else "selected_offset_span_missing_or_out_of_bounds"
            )
        else:
            evidence_reason = "no_selected_candidates"
    evidence_present = bool(evidence_ids)
    return {
        "status": "provider_reported_selected" if selected else "provider_reported_rejected_all",
        "selected_candidate_ids": selected,
        "rejection_reason_codes": rejected,
        "reasoning_discipline_ids": sorted(disciplines),
        "application_evidence_present": evidence_present,
        "application_evidence_candidate_ids": evidence_ids,
        "application": "provider_asserted_span_present" if evidence_present else "not_observed",
        "application_evidence_reason": evidence_reason,
    }

def build_adjudication_output_contract(candidates: Any) -> str:
    """Describe the bounded report; selected evidence is an exact verbatim answer substring."""
    index = _candidate_index(candidates)
    if not index:
        return ""
    ids = ", ".join(sorted(index))
    reasons = ", ".join(sorted(REASON_CODES))
    # Keep this contract compact: it is repeated in every provider prompt and
    # competes with visitor evidence for finite context/token budgets.
    return (
        "Add JSON property adaptive_adjudication with exactly two keys: "
        "candidate_assessments and application_evidence_quotes. For every candidate "
        "ID (" + ids + "), emit exactly one assessment object with candidate_id, "
        "decision (select/reject), and reason_code (empty string for select; one of " + reasons +
        " for reject). Assess activation scope and abstention boundary; accept semantically equivalent "
        "questions. Select only distinct, relevant candidates. After drafting the final response, emit one quote object per candidate: selected IDs use an exact verbatim 12–120-character substring from the final response that shows the distinctive operation; rejected IDs use an empty quote; reject-all uses empty quotes. The runtime locates the quote itself, so do not count character offsets or paraphrase. Prefer few candidates. "
        "No hidden reasoning or chain-of-thought. "
        "This report is not visitor-facing and is not proof of semantic quality; "
        "the runtime validates IDs, complete disposition, reason codes, and quoted evidence, then verifies "
        "the exact quote occurs once in the final answer. Improvement still requires paired evaluation. "
        "Output one object, not adjudication alone: "
        '{"response":"complete visitor answer","doorway_title":"title or empty",'
        '"response_shape":"shape","adaptive_adjudication":'
        '{"candidate_assessments":[...],"application_evidence_quotes":[...]}}.'
    )
