"""Inquiry-family classification and Gold Star transfer compatibility.

This module is deliberately dependency-light so retrieval, question contracts,
and response validation can share one conservative boundary without cycles.
A detected family is a routing constraint, not a claim of psychological diagnosis.
"""
from __future__ import annotations

import re
from typing import Any, Dict

_VERSION = "1.0"

_LIVED_SUBJECT = re.compile(
    r"\b(?:pain|suffer\w*|hurt|grief|loss|bereave\w*|mourning|trauma|"
    r"shame|fear|loneliness|heartbreak|wound\w*|identity|selfhood|personhood|"
    r"belonging|who i am|sense of self)\b",
    re.I,
)
_IDENTITY_FOCUS = re.compile(r"\b(?:identity|selfhood|personhood|belonging|who i am|sense of self|defined by|total identity)\b", re.I)
_LIVED_FRAME = re.compile(
    r"\b(?:hold|carry|bear|live with|cope with|make sense of|process|"
    r"turn(?:ing)? into|become|define|identify with|feel|experience|"
    r"reconcile|integrate|heal|recover|remain|stay)\b",
    re.I,
)
# Keep this a three-signal boundary: a metaphysical subject, a request or
# implication of certainty, and a credible vulnerability/loss cue. The second
# branch captures ordinary visitor language (e.g. bereavement + "is she
# somewhere?") without requiring clinical or philosophical vocabulary.
_EPISTEMIC_DISTRESS = re.compile(
    r"(?=.*\\b(?:metaphysical|spiritual|ultimate|existential|afterlife|life after death|"
    r"soul|heaven|hell|divine|god|consciousness|death|die|died|what happens after death)\\b)"
    r"(?=.*\\b(?:certainty|certain|truth|proof|know for sure|can anyone know|need to know|"
    r"is there|does .{1,45} exist|is .{1,45} real|is .{1,45} somewhere|"
    r"gone forever|never see .{1,45} again)\\b)"
    r"(?=.*\\b(?:distress|distressed|fear|grief|loss|bereave\\w*|mourning|"
    r"panic|overwhelmed|vulnerable|suffering|frighten\\w*|anxious|anxiety|"
    r"desperate|died|death of|gone|scared|terrified)\\b).*",
    re.I,
)

_GUIDE_RESPONSE_REQUEST = re.compile(
    r"\b(?:guide|assistant)\b.{0,100}\b(?:respond|answer|handle|support)\b"
    r"|\bhow should\b.{0,80}\b(?:guide|assistant)\b",
    re.I,
)

_GOVERNANCE_QUERY = re.compile(r"\b(?:community|communities|organization|organisation|institution|team|board|policy|rule|governance|stakeholder)\b", re.I)
_GOVERNANCE_ACTION = re.compile(r"\b(?:decision|decide|authority|accountability|responsibility|outcome|rule|policy|tradeoff|limits?|restrict|allocate)\b", re.I)

_GOVERNANCE_FAMILY = re.compile(
    r"(?:governance|institution|organiz|community|stakeholder|decision|"
    r"accountab|power|authority|rule|policy|tradeoff|trade_off|"
    r"ethical_governance|systems_consequence|preaction)",
    re.I,
)


def classify_inquiry_family(query: str) -> Dict[str, Any]:
    """Identify a narrow lived/reflective family before generic task verbs."""
    text = re.sub(r"\s+", " ", str(query or "")).strip()
    if not text:
        return {"version": _VERSION, "family": "unknown", "confidence": "none", "signals": [], "identity_focus": False}
    if _EPISTEMIC_DISTRESS.search(text):
        family = "epistemic_distress_guidance" if _GUIDE_RESPONSE_REQUEST.search(text) else "epistemic_distress"
        return {
            "version": _VERSION,
            "family": family,
            "confidence": "high",
            "signals": ["metaphysical_or_spiritual_claim", "certainty_seeking", "distress_or_vulnerability"],
            "identity_focus": False,
        }
    if _GOVERNANCE_QUERY.search(text) and _GOVERNANCE_ACTION.search(text):
        return {"version": _VERSION, "family": "institutional_governance", "confidence": "high", "signals": ["governance_subject", "governance_action"], "identity_focus": bool(_IDENTITY_FOCUS.search(text))}
    subject = _LIVED_SUBJECT.search(text)
    frame = _LIVED_FRAME.search(text)
    if subject and frame:
        return {
            "version": _VERSION,
            "family": "personal_lived_reflective",
            "confidence": "high",
            "signals": [subject.group(0).casefold(), frame.group(0).casefold()],
            "identity_focus": bool(_IDENTITY_FOCUS.search(text)),
        }
    return {"version": _VERSION, "family": "unknown", "confidence": "none", "signals": [], "identity_focus": False}


def lesson_transfer_compatibility(query: str, lesson: Any) -> Dict[str, Any]:
    """Fail closed when a lived inquiry is paired with an institutional lesson."""
    inquiry = classify_inquiry_family(query)
    family = inquiry["family"]
    reasoning_family = str((lesson or {}).get("reasoning_family") or "").strip()
    if family in {"epistemic_distress", "epistemic_distress_guidance"}:
        allowed = {"humane_orientation", "epistemic_humility_under_distress"}
        if reasoning_family in allowed:
            return {"compatible": True, "reason": "approved_epistemic_distress_family", "inquiry_family": family}
        return {
            "compatible": False,
            "reason": "cross_family_transfer_blocked",
            "inquiry_family": family,
            "lesson_family": reasoning_family or "unknown",
        }
    if family != "personal_lived_reflective":
        return {"compatible": True, "reason": "no_lived_family_boundary", "inquiry_family": family}
    q = str(query or "").casefold()
    # The broad humane-orientation lesson is the only default candidate for
    # a lived inquiry. More specialized lessons require their own explicit
    # subject cues; identity or pain vocabulary alone cannot activate them.
    allowed = {"humane_orientation"}
    if re.search(r"\b(?:relationship|relational|development|social conditions|community support)\b", q):
        allowed.add("relational_human_development_with_epistemic_boundary")
    if re.search(r"\b(?:inherit\w*|legacy|family history|harmful pattern|past generations)\b", q):
        allowed.add("continuity_without_preserving_harmful_inheritance")
    if re.search(r"\b(?:therapy|therapist|clinical|professional care|self.inquiry|reflection)\b", q):
        allowed.add("reflection_orientation_vs_therapy_professional_boundary")
    if re.search(r"\b(?:felt true|feels true|belief|claim|resonat|emotionally compelling)\b", q):
        allowed.add("felt_truth_claim_discernment")
    if re.search(r"\b(?:soul|oversoul|personality)\b", q):
        allowed.add("personality_soul_oversoul_discernment")
    if reasoning_family in allowed and not _GOVERNANCE_FAMILY.search(reasoning_family):
        return {
            "compatible": True,
            "reason": "approved_lived_reflective_family",
            "inquiry_family": family,
        }
    return {
        "compatible": False,
        "reason": "cross_family_transfer_blocked",
        "inquiry_family": family,
        "lesson_family": reasoning_family or "unknown",
    }
