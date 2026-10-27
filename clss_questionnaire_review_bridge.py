"""Explicit bridge from questionnaire normalization to human-confirmed CLSS review.

This bridge is session-local. It never creates a contextual judgment from raw
answers: callers must provide a separate review object with explicit judgments.
It performs no network calls and no persistence.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from clss_contextual_review import compose_contextual_review
from clss_evidence_normalization import normalize_questionnaire_answers


class CLSSQuestionnaireReviewBridgeError(ValueError):
    """Raised when normalized questionnaire data cannot enter contextual review."""


def normalize_and_review(
    answers: Sequence[Mapping[str, Any]],
    review: Mapping[str, Any],
    *,
    mode: str,
) -> dict[str, Any]:
    """Normalize answers, then compose only from a separately supplied review.

    The returned envelope keeps missing questionnaire dimensions visible as
    gaps alongside (not inside) the canonical visitor response.
    """
    if not isinstance(review, Mapping):
        raise CLSSQuestionnaireReviewBridgeError(
            "an explicit contextual review object is required; raw answers are not a judgment"
        )
    normalized = normalize_questionnaire_answers(answers, mode=mode)
    if not normalized["evidence"]:
        raise CLSSQuestionnaireReviewBridgeError(
            "no answered evidence is available; do not manufacture a finding"
        )
    response = compose_contextual_review(
        normalized["evidence"],
        review,
        mode=normalized["mode"],
    )
    return {
        "response": response,
        "missing_dimensions": normalized["missing_dimensions"],
        "normalization_notes": normalized["normalization_notes"],
        "review_required": True,
    }
