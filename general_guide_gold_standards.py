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
    text = str(value or "").translate(str.maketrans({
        "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-",
        "\u2014": "-", "\u2212": "-", "\u2018": "'", "\u2019": "'",
        "\u02bc": "'", "\uff07": "'",
    }))
    normalized = re.sub(r"\s+", " ", text).strip().casefold()
    normalized = re.sub(r"[?.!]+$", "", normalized).strip()
    return normalized


def load_approved_standards() -> Dict[str, Dict[str, str]]:
    """Load exact approved answers and explicitly authorized exact-query release candidates."""
    payload = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("Gold-standard registry records must be a list.")

    standards: Dict[str, Dict[str, str]] = {}
    for record in records:
        if not isinstance(record, dict) or record.get("status") not in _ELIGIBLE_STATUSES:
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
        no_handoff = intentionally_none or any(
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
                or bool(previous.get("forbids_doorway")) != no_handoff
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
            "forbids_doorway": no_handoff,
        }
    return standards


def resolve_exact_gold_standard(question: str) -> Optional[Dict[str, str]]:
    normalized = _normalize_question(question)
    if not normalized:
        return None
    return load_approved_standards().get(normalized)


def find_cross_question_standard_response(question: str, response: str) -> Optional[Dict[str, str]]:
    normalized_question = _normalize_question(question)
    normalized_response = str(response or "").strip()
    if not normalized_question or not normalized_response:
        return None
    for standard_question, record in load_approved_standards().items():
        if record.get("status") != "USER_APPROVED_GOLD_STANDARD":
            continue
        if standard_question == normalized_question:
            continue
        if record["expected_response"].strip() == normalized_response:
            return {**record, "standard_question": standard_question}
    return None
