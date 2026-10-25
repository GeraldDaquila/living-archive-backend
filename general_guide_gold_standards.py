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
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


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
        if question in standards and standards[question]["expected_response"] != answer:
            raise ValueError(
                "Conflicting approved gold-standard answers share an exact question."
            )
        standards[question] = {
            "expected_response": answer,
            "benchmark_id": str(record.get("benchmark_id") or ""),
            "status": str(record.get("status") or ""),
        }
    return standards


def resolve_exact_gold_standard(question: str) -> Optional[Dict[str, str]]:
    """Resolve only an exact normalized question; never fuzzy-match a benchmark."""
    normalized = _normalize_question(question)
    if not normalized:
        return None
    return load_approved_standards().get(normalized)
