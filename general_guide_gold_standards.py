"""Exact-match runtime enforcement for approved General Guide standards.

Only records explicitly frozen as reference standards or approved by the user
are eligible. Recovered historical responses, candidates, and diagnostic
fixtures remain evaluation material, not production answer authority.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

_REGISTRY_PATH = Path(__file__).resolve().parent / "docs" / "qa" / "gold_standard_registry.json"
_ELIGIBLE_STATUSES = {"FROZEN_REFERENCE_ONLY", "USER_APPROVED_GOLD_STANDARD"}


def _normalize_question(value: Any) -> str:
    # Browsers, keyboards, and text pipelines can change typographic apostrophes
    # without changing the visitor's question. Canonicalize those variants so
    # exact approved standards still apply, while keeping matching non-fuzzy.
    text = str(value or "").translate(str.maketrans({
        "\u2018": "'",
        "\u2019": "'",
        "\u02bc": "'",
        "\uff07": "'",
    }))
    normalized = re.sub(r"\s+", " ", text).strip().casefold()
    # Treat terminal question punctuation as presentation, not a different
    # question. Some request paths normalize it away before final resolution.
    return re.sub(r"[?.!]+$", "", normalized).strip()


def load_approved_standards() -> Dict[str, Dict[str, str]]:
    """Load exact approved/frozen answers keyed by normalized benchmark question."""
    payload = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("Gold-standard registry records must be a list.")

    standards: Dict[str, Dict[str, str]] = {}
    for record in records:
        if not isinstance(record, dict) or record.get("status") not in _ELIGIBLE_STATUSES:
            continue
        question = _normalize_question(record.get("query"))
        answer = str(record.get("expected_response") or "").strip()
        if not question or not answer:
            continue
        doorway = record.get("expected_doorway") or {}
        assertions = record.get("assertions") or []
        no_handoff = any(
            "forbids direct page handoff" in str(assertion).casefold()
            for assertion in assertions
        ) or bool(re.search(r"\bdo not send me to another page\b", question))
        doorway_title = "" if no_handoff else str(doorway.get("title") or "")
        doorway_url = None if no_handoff else doorway.get("url")
        if question in standards:
            previous = standards[question]
            if previous["expected_response"] != answer:
                raise ValueError(
                    "Conflicting approved gold-standard answers share an exact question."
                )
            if (
                previous.get("doorway_title", "") != doorway_title
                or previous.get("doorway_url", "") != (str(doorway_url) if doorway_url else "")
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
