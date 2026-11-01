"""Isolated CLSS hybrid-synthesis adapter.

This module is deliberately not wired to the USE gateway or WordPress. It
prepares a minimized evidence payload only after explicit, versioned consent,
accepts an injected candidate builder for offline/mock evaluation, and marks
all model candidates as unverified until separate semantic review passes.

No provider credentials, HTTP client, logging, persistence, or telemetry live
here. A future transport adapter must be separately authorized and audited.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from clss_evidence_normalization import normalize_questionnaire_answers
from tests.clss_deterministic_response import build_deterministic_response
from tests.clss_response_validator import validate_or_fallback

CONSENT_PURPOSE = "clss_synthesis"
CONSENT_NOTICE_VERSION = "clss-synthesis-notice-v1"
MAX_ANSWER_CHARS = 4000
MAX_TOTAL_CHARS = 16000
MAX_EVIDENCE_ITEMS = 8

CandidateBuilder = Callable[[Mapping[str, Any]], Mapping[str, Any]]


class CLSSHybridSynthesisError(ValueError):
    """Raised when the synthesis request violates its bounded contract."""


def _has_consent(consent: Mapping[str, Any] | None) -> bool:
    return bool(
        isinstance(consent, Mapping)
        and consent.get("granted") is True
        and consent.get("purpose") == CONSENT_PURPOSE
        and consent.get("notice_version") == CONSENT_NOTICE_VERSION
    )


def build_minimized_candidate_request(
    normalized: Mapping[str, Any],
    *,
    consent: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Create a bounded request payload; never transmit or persist it here."""
    if not _has_consent(consent):
        raise CLSSHybridSynthesisError("explicit CLSS synthesis consent is required")
    mode = normalized.get("mode")
    if mode not in {"self", "third_party"}:
        raise CLSSHybridSynthesisError("normalized mode is invalid")
    evidence = normalized.get("evidence")
    if not isinstance(evidence, Sequence) or isinstance(evidence, (str, bytes)):
        raise CLSSHybridSynthesisError("normalized evidence must be a sequence")
    if not evidence or len(evidence) > MAX_EVIDENCE_ITEMS:
        raise CLSSHybridSynthesisError("evidence count is outside the allowed bound")

    minimized = []
    total_chars = 0
    seen_ids = set()
    for item in evidence:
        if not isinstance(item, Mapping):
            raise CLSSHybridSynthesisError("evidence item must be an object")
        evidence_id = item.get("evidence_id")
        text = item.get("answer_text")
        if not isinstance(evidence_id, str) or not evidence_id or evidence_id in seen_ids:
            raise CLSSHybridSynthesisError("evidence IDs must be unique non-empty strings")
        if not isinstance(text, str) or not text.strip():
            raise CLSSHybridSynthesisError("evidence answer text must be non-empty")
        if len(text) > MAX_ANSWER_CHARS:
            raise CLSSHybridSynthesisError("an answer exceeds the per-answer size limit")
        total_chars += len(text)
        if total_chars > MAX_TOTAL_CHARS:
            raise CLSSHybridSynthesisError("evidence exceeds the total text size limit")
        seen_ids.add(evidence_id)
        provenance = item.get("provenance")
        if not isinstance(provenance, Mapping) or provenance.get("mode") != mode:
            raise CLSSHybridSynthesisError("evidence provenance must match the selected perspective")
        source_type = item.get("source_type", "unknown")
        dimension = item.get("dimension", "unknown")
        minimized.append({
            "evidence_id": evidence_id,
            "prompt_id": str(item.get("prompt_id") or ""),
            "dimension": str(dimension),
            "source_type": str(source_type),
            "answer_text": text,
            "provenance": {
                "mode": mode,
                "source_type_was_explicit": provenance.get("source_type_was_explicit") is True,
            },
        })

    return {
        "contract_version": "clss-hybrid-candidate-v1",
        "purpose": CONSENT_PURPOSE,
        "notice_version": CONSENT_NOTICE_VERSION,
        "mode": mode,
        "evidence": minimized,
        "missing_dimensions": list(normalized.get("missing_dimensions") or []),
        "constraints": [
            "Treat supplied answers as unverified respondent accounts, not established facts.",
            "Cite only supplied evidence IDs; do not invent or alter evidence.",
            "Keep source provenance, uncertainty, context, and counterevidence distinct.",
            "Missing information is an information gap, never adverse evidence.",
            "Do not infer private motives, diagnose, score, rank, or decide suitability.",
            "If a defensible relationship is not established, say so explicitly.",
        ],
    }


def resolve_hybrid_candidate(
    answers: Sequence[Mapping[str, Any]],
    *,
    mode: str,
    consent: Mapping[str, Any] | None,
    candidate_builder: CandidateBuilder | None = None,
) -> dict[str, Any]:
    """Return an offline-evaluable candidate envelope with a deterministic fallback.

    The injected builder is called only after consent validation. Even a
    structurally valid candidate remains non-displayable pending semantic review.
    """
    normalized = normalize_questionnaire_answers(answers, mode=mode)
    evidence = normalized["evidence"]
    if not evidence:
        raise CLSSHybridSynthesisError("no answered evidence; no finding may be manufactured")

    fallback = build_deterministic_response(
        evidence,
        mode=mode,
        missing_dimensions=normalized["missing_dimensions"],
    )
    if not _has_consent(consent) or candidate_builder is None:
        return {
            "response": fallback,
            "path": "deterministic_fallback",
            "semantic_status": "not_evaluated",
            "human_review_required": False,
            "provider_invoked": False,
        }

    request = build_minimized_candidate_request(normalized, consent=consent)
    candidate = None
    try:
        candidate = candidate_builder(request)
    except Exception:
        candidate = None
    selected, path = validate_or_fallback(
        candidate,
        fallback,
        {item["evidence_id"] for item in evidence},
        mode=mode,
    )
    return {
        "response": selected,
        "path": path,
        "semantic_status": "unverified_candidate" if path == "llm" else "not_evaluated",
        "human_review_required": path == "llm",
        "provider_invoked": True,
        "transmission_performed": False,
    }
