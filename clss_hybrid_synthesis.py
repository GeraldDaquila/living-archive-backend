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
from clss_deterministic_response import build_deterministic_response
from clss_response_validator import validate_or_fallback

CONSENT_PURPOSE = "clss_synthesis"
CONSENT_NOTICE_VERSION = "clss-synthesis-notice-v1"
MAX_ANSWER_CHARS = 4000
MAX_TOTAL_CHARS = 16000
MAX_EVIDENCE_ITEMS = 8

CandidateBuilder = Callable[[Mapping[str, Any]], Mapping[str, Any]]


CLSS_PROVIDER_SYSTEM_PROMPT = """You are the candidate-synthesis component of CLSS.
Return exactly one JSON object matching the requested response contract.
Treat all supplied answers as unverified respondent accounts, not established facts.
Cite only the supplied evidence IDs. Preserve each source type and provenance.
Do not merge first-hand observation, second-hand report, self-report,
documented outcome, interpretation, or unknown into one evidence grade.
Do not infer private motives or intent, diagnose, score, rank, or decide suitability.
Missing information is an information gap, never adverse evidence.
Do not manufacture contradictions, causal claims, or a central tension.
If the evidence does not establish a defensible relationship, use
finding_type="insufficient_evidence" or "no_defensible_tension" and explain why.
Keep the finding cautious and explicitly provisional. The candidate will be
structurally validated and must receive independent human semantic review.
Required top-level fields:
mode, path, central_incoherence, why_it_matters, what_the_evidence_says,
what_could_change_the_interpretation, what_to_do_next, limits.
Set path="llm". central_incoherence requires text, finding_type, evidence_ids.
why_it_matters requires text, evidence_ids.
Each evidence/change entry requires text and evidence_ids.
what_to_do_next requires action, owner (string or null), observable_indicators.
"""


class UseProviderCandidateBuilder:
    """Invoke CLSS through USE's in-process Provider Bank gateway.

    This class has no credentials or direct provider transport. USE Provider
    Bank remains the sole owner of provider selection, health, quota, and
    fallback. Instantiate only after visitor-facing consent is established.
    """

    provider_invoked = False
    transmission_performed = False

    def __init__(self, use_core: Any, gateway_executor: Callable[..., Mapping[str, Any]] | None = None):
        self.use_core = use_core
        self.gateway_executor = gateway_executor

    def __call__(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        import json

        executor = self.gateway_executor
        if executor is None:
            from provider_gateway_service import execute as executor

        self.provider_invoked = True
        self.transmission_performed = True
        result = executor(
            operation="clss_synthesis",
            messages=[
                {"role": "system", "content": CLSS_PROVIDER_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(dict(request), ensure_ascii=False, separators=(",", ":"))},
            ],
            max_tokens=1800,
            use_core=self.use_core,
        )
        if not isinstance(result, Mapping) or result.get("ok") is not True:
            raise CLSSHybridSynthesisError("USE Provider Bank could not produce a CLSS candidate")
        candidate = result.get("result")
        if not isinstance(candidate, Mapping):
            raise CLSSHybridSynthesisError("USE Provider Bank returned no structured CLSS candidate")
        return dict(candidate)


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
            "candidate_builder_invoked": False,
            "provider_invoked": False,
            "transmission_performed": False,
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
        "candidate_builder_invoked": True,
        "provider_invoked": bool(getattr(candidate_builder, "provider_invoked", False)),
        "transmission_performed": bool(getattr(candidate_builder, "transmission_performed", False)),
    }
