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
_LIVED_FRAME = re.compile(
    r"\b(?:hold|carry|bear|live with|cope with|make sense of|process|"
    r"turn(?:ing)? into|become|define|identify with|feel|experience|"
    r"reconcile|integrate|heal|recover|remain|stay)\b",
    re.I,
)
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
        return {"version": _VERSION, "family": "unknown", "confidence": "none", "signals": []}
    subject = _LIVED_SUBJECT.search(text)
    frame = _LIVED_FRAME.search(text)
    if subject and frame:
        return {
            "version": _VERSION,
            "family": "personal_lived_reflective",
            "confidence": "high",
            "signals": [subject.group(0).casefold(), frame.group(0).casefold()],
        }
    return {"version": _VERSION, "family": "unknown", "confidence": "none", "signals": []}


def lesson_transfer_compatibility(query: str, lesson: Any) -> Dict[str, Any]:
    """Fail closed when a lived inquiry is paired with an institutional lesson."""
    inquiry = classify_inquiry_family(query)
    family = inquiry["family"]
    reasoning_family = str((lesson or {}).get("reasoning_family") or "").strip()
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
