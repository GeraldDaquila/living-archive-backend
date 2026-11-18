"""Exact-match runtime enforcement for approved General Guide standards.

Only records explicitly approved by the user are eligible. Historical
references, recovered responses, candidates, and diagnostic fixtures remain
evaluation or provenance material, not production answer authority.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

_REGISTRY_PATH = Path(__file__).resolve().parent / "docs" / "qa" / "gold_standard_registry.json"
_ELIGIBLE_STATUSES = {
    "USER_APPROVED_GOLD_STANDARD",
    # Explicit release candidates may be served only for exact-query live review.
    # They are deliberately excluded from Gold Star learning and count authority.
    "USER_APPROVED_RELEASE_CANDIDATE",
}


def _normalize_question(value: Any) -> str:
    # Browsers, keyboards, and text pipelines can change typographic apostrophes
    # without changing the visitor's question. Canonicalize those variants so
    # exact approved standards still apply, while keeping matching non-fuzzy.
    text = str(value or "").translate(str.maketrans({
        # Normalize browser/editor dash variants so an exact visitor question
        # cannot bypass an approved release review merely because typography
        # changed in transit.
        "\u2010": "-",  # hyphen
        "\u2011": "-",  # non-breaking hyphen
        "\u2012": "-",  # figure dash
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u2212": "-",  # minus sign
        "\u2018": "'",
        "\u2019": "'",
        "\u02bc": "'",
        "\uff07": "'",
    }))
    normalized = re.sub(r"\s+", " ", text).strip().casefold()
    # Some browser and transport paths retain harmless terminal whitespace or
    # punctuation variants. Remove terminal punctuation and collapse any
    # whitespace exposed by that removal before exact registry lookup.
    normalized = re.sub(r"[?.!]+$", "", normalized).strip()
    return normalized


def load_approved_standards() -> Dict[str, Dict[str, str]]:
    """Load exact approved answers and explicitly authorized exact-query release candidates."""
    payload = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("Gold-standard registry records must be a list.")

    records_by_id = {
        str(record.get("benchmark_id") or ""): record
        for record in records
        if isinstance(record, dict)
    }
    standards: Dict[str, Dict[str, str]] = {}
    for record in records:
        if not isinstance(record, dict) or record.get("status") not in _ELIGIBLE_STATUSES:
            continue
        # A Gold Star may remain an approved structural-learning exemplar while
        # a governed exact-query release candidate temporarily owns its runtime
        # answer. Validate both sides of that explicit relationship and exclude
        # only the predecessor from exact-answer lookup; never demote the Gold Star.
        successor_id = str(record.get("runtime_exact_query_successor") or "").strip()
        if successor_id:
            successor = records_by_id.get(successor_id)
            successor_capabilities = (
                successor.get("gold_star_capabilities") or {}
                if isinstance(successor, dict)
                else {}
            )
            valid_successor = bool(
                isinstance(successor, dict)
                and successor.get("replaces_exact_query_runtime_authority_of")
                    == record.get("benchmark_id")
                and _normalize_question(successor.get("query"))
                    == _normalize_question(record.get("query"))
                and successor.get("status") in _ELIGIBLE_STATUSES
                and successor_capabilities.get("exact_answer_authority") is True
            )
            if not valid_successor:
                raise ValueError(
                    "Gold Star runtime exact-query successor linkage is invalid: "
                    + str(record.get("benchmark_id") or "")
                )
            continue
        capabilities = record.get("gold_star_capabilities") or {}
        if capabilities and not bool(capabilities.get("exact_answer_authority")):
            continue
        question = _normalize_question(record.get("query"))
        answer = str(record.get("expected_response") or "").strip()
        if not question or not answer:
            continue
        raw_doorway = record.get("expected_doorway")
        doorway_status = str(record.get("doorway_status") or "").strip()
        intentionally_none = doorway_status == "INTENTIONALLY_NONE_APPROVED"
        if intentionally_none and raw_doorway is not None:
            raise ValueError(
                "An intentionally-none Gold Standard cannot also declare an expected doorway."
            )
        doorway = raw_doorway or {}
        assertions = record.get("assertions") or []
        legacy_no_doorway_assertion = any(
            (
                "do not attach an unrelated archive doorway or recommendation"
                in str(assertion).casefold()
                and "self-contained factual question" in str(assertion).casefold()
            )
            for assertion in assertions
        )
        legacy_doorway_not_authorized = bool(
            doorway_status == "LEGACY_INCOMPLETE_NOT_APPROVED"
            and raw_doorway is None
            and str(record.get("doorway_note") or "").strip()
            and legacy_no_doorway_assertion
        )
        no_handoff = intentionally_none or legacy_doorway_not_authorized or any(
            "forbids direct page handoff" in str(assertion).casefold()
            for assertion in assertions
        ) or bool(re.search(r"\bdo not send me to another page\b", question))
        doorway_title = "" if no_handoff else str(doorway.get("title") or "")
        doorway_url = None if no_handoff else doorway.get("url")
        doorway_rationale = "" if no_handoff else str(doorway.get("rationale") or "").strip()
        doorway_omission_reason = str(
            record.get("doorway_omission_exception_reason")
            or (record.get("doorway_note") if legacy_doorway_not_authorized else "")
            or ""
        ).strip()
        if question in standards:
            previous = standards[question]
            if previous["expected_response"] != answer:
                raise ValueError(
                    "Conflicting approved gold-standard answers share an exact question."
                )
            if (
                previous.get("doorway_title", "") != doorway_title
                or previous.get("doorway_url", "") != (str(doorway_url) if doorway_url else "")
                or previous.get("doorway_rationale", "") != doorway_rationale
                or bool(previous.get("forbids_doorway")) != no_handoff
                or previous.get("doorway_omission_exception_reason", "")
                    != (str(record.get("doorway_omission_exception_reason") or "").strip() if no_handoff else "")
            ):
                raise ValueError(
                    "Conflicting approved gold-standard doorways share an exact question."
                )
            continue
        standards[question] = {
            "expected_response": answer,
            "benchmark_id": str(record.get("benchmark_id") or ""),
            "status": str(record.get("status") or ""),
            "doorway_title": doorway_title,
            "doorway_url": str(doorway_url) if doorway_url else "",
            "doorway_rationale": doorway_rationale,
            "forbids_doorway": no_handoff,
            "doorway_omission_exception_reason": (
                doorway_omission_reason if no_handoff else ""
            ),
        }
    return standards


def resolve_exact_gold_standard(question: str) -> Optional[Dict[str, str]]:
    """Resolve only an exact normalized question; never fuzzy-match a benchmark."""
    normalized = _normalize_question(question)
    if not normalized:
        return None
    return load_approved_standards().get(normalized)


def find_cross_question_standard_response(question: str, response: str) -> Optional[Dict[str, str]]:
    """Find an approved answer reused for a different question.

    This is a final-boundary integrity check, not a fuzzy answer matcher. It
    only flags exact approved answer text and only when the incoming question
    is not that record's exact normalized question.
    """
    normalized_question = _normalize_question(question)
    normalized_response = str(response or "").strip()
    if not normalized_question or not normalized_response:
        return None
    for standard_question, record in load_approved_standards().items():
        # Frozen reference-only answers are reusable as deliberate exact-query
        # fixtures, but are not all formally approved as universal cross-query
        # sentinels. Only explicitly user-approved Gold Standards participate
        # in this leakage detector.
        if record.get("status") != "USER_APPROVED_GOLD_STANDARD":
            continue
        if standard_question == normalized_question:
            continue
        if record["expected_response"].strip() == normalized_response:
            return {**record, "standard_question": standard_question}
    return None
