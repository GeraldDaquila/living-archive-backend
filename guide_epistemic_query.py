"""Bounded multi-axis epistemic query decomposition for The Guide.

This module improves retrieval recall for questions that ask how several
epistemic categories relate. It does not assert Archive doctrine, select a
resource, or authorize a doorway. The original visitor question remains the
answer/composition authority.
"""
from __future__ import annotations

import re
from typing import Any

VERSION = "1.0"

_AXIS_PATTERNS = {
    "evidence": (
        r"\\bevidence\\b",
        r"\\bfacts?\\b",
        r"\\bobservations?\\b",
        r"\\bsources?\\b",
    ),
    "interpretation": (
        r"\\binterpretations?\\b",
        r"\\binferences?\\b",
        r"\\bmeaning[- ]making\\b",
        r"\\bmeaning\\b",
    ),
    "hypothesis": (
        r"\\bhypotheses?\\b",
        r"\\bprovisional explanations?\\b",
        r"\\btestable explanations?\\b",
        r"\\btheories?\\b",
    ),
    "normative_judgment": (
        r"\\bnormative judg(?:e)?ments?\\b",
        r"\\bvalue[- ]judg(?:e)?ments?\\b",
        r"\\bwhat ought to be\\b",
        r"\\bwhat should be\\b",
    ),
}

_RELATIONAL_INTENT = (
    r"\\bwhat counts as\\b",
    r"\\bdistinguish(?:es|ing)?\\b",
    r"\\bdifference(?:s)? between\\b",
    r"\\bhow do .{0,80} differ\\b",
    r"\\bseparate .{0,80} from\\b",
    r"\\brelationship between\\b",
    r"\\bcompare\\b",
)

_AXIS_RETRIEVAL_LANGUAGE = {
    "evidence": "observable evidence, source quality, provenance, corroboration, and factual observations",
    "interpretation": "interpretation, inference, meaning-making, and the distinction between what is observed and what is inferred",
    "hypothesis": "hypotheses as provisional, testable explanations that may be supported or revised by evidence",
    "normative_judgment": "normative or value judgments, ethical evaluation, and claims about what ought to be",
}


def build_epistemic_retrieval_plan(query: str) -> dict[str, Any] | None:
    """Return a bounded retrieval plan for genuinely multi-axis epistemic questions."""
    raw = re.sub(r"\\s+", " ", str(query or "")).strip()
    if not raw or not re.search(r"[?]", raw):
        return None
    if not any(re.search(pattern, raw, re.I) for pattern in _RELATIONAL_INTENT):
        return None

    axes = [
        axis for axis, patterns in _AXIS_PATTERNS.items()
        if any(re.search(pattern, raw, re.I) for pattern in patterns)
    ]
    if len(axes) < 3:
        return None

    # Keep the plan short and deterministic. This is a retrieval formulation,
    # not generated evidence and not a replacement for the visitor's question.
    retrieval_query = (
        "Epistemic distinctions and relationships: "
        + "; ".join(_AXIS_RETRIEVAL_LANGUAGE[axis] for axis in axes)
        + ". Distinguish descriptive claims from interpretive inferences, "
          "provisional explanatory hypotheses, and normative or ethical judgments. "
          "Examine claim provenance, uncertainty, corroboration, and what evidence "
          "would support, challenge, or revise each kind of claim."
    )
    return {
        "version": VERSION,
        "mode": "bounded_multi_axis_epistemic",
        "axes": axes,
        "axis_count": len(axes),
        "retrieval_query": retrieval_query,
        "original_query_preserved": True,
        "doorway_authority": "unchanged_existing_canonical_gates",
    }


__all__ = ["VERSION", "build_epistemic_retrieval_plan"]
