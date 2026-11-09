"""Shadow-mode observability for Gold Star lesson selection.

This module intentionally does not alter visitor answers. It exposes a compact
selection record for QA and controlled runtime integration.
"""
from __future__ import annotations

from typing import Any, Dict

from gold_star_lessons import select_exemplar

SHADOW_MODE_DEFAULT = True


def evaluate_gold_star_shadow(query: str) -> Dict[str, Any]:
    exemplar = select_exemplar(query)
    if exemplar is None:
        return {
            "gold_star_shadow": True,
            "selected": False,
            "benchmark_id": "",
            "score": 0.0,
            "reason": "abstained",
        }
    return {
        "gold_star_shadow": True,
        "selected": True,
        "benchmark_id": str(exemplar.get("benchmark_id") or ""),
        "score": float(exemplar.get("score") or 0.0),
        "reason": "high_confidence_structural_match",
    }
