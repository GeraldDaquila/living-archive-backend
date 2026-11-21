"""Held-out evaluation contract for Gold Star structural learning.

This module does not compose visitor answers. It compares the current selector
against fixed expected benchmark IDs held separately from the selector's
candidate pool. Tests may replace the candidate pool without changing the
expected outcomes.
"""
from __future__ import annotations

from typing import Dict, Iterable, List

import gold_star_lessons as lessons

HELD_OUT_CASES: List[Dict[str, object]] = [
    {
        "name": "approved related variant",
        "query": "How should we understand personal responsibility when circumstances limit people's choices?",
        "expected_id": "general-guide-agency-circumstance-gold-star-2026-11-09",
    },
    {
        "name": "nearby but unsupported topic",
        "query": "Why do organizations sometimes avoid responsibility when outcomes are uncertain?",
        "expected_id": None,
    },
    {
        "name": "unrelated question",
        "query": "How do I calculate the area of a triangle?",
        "expected_id": None,
    },
]


def evaluate(cases: Iterable[Dict[str, object]] = HELD_OUT_CASES) -> Dict[str, object]:
    """Evaluate the current selector against fixed expectations.

    Each call invokes the live selector, so test-only selector substitution is
    possible. Expected IDs remain independent immutable evaluation data.
    """
    results = []
    passed = True
    for case in cases:
        result = lessons.select_lesson(str(case["query"]))
        actual = result["benchmark_id"] if result else None
        ok = actual == case["expected_id"]
        results.append({
            "name": case["name"],
            "expected_id": case["expected_id"],
            "actual_id": actual,
            "passed": ok,
        })
        passed = passed and ok
    return {"passed": passed, "results": results}
