"""Sitewide Safety / Crisis utility for The Guide."""
from __future__ import annotations
import re
from typing import Any, Mapping

SAFETY_UTILITY_VERSION = "v1"

_RED_PATTERNS = (
    re.compile(r"\b(?:i(?:'m| am)?\s+going\s+to|i(?:'m| am)?\s+about\s+to|i\s+will)\s+(?:kill|end)\s+(?:myself|my\s+life)\b", re.I),
    re.compile(r"\b(?:i\s+want\s+to|i(?:'m| am)?\s+thinking\s+about)\s+(?:kill(?:ing)?\s+myself|ending\s+my\s+life|taking\s+my\s+own\s+life|harming\s+myself|hurting\s+myself)\b", re.I),
    re.compile(r"\b(?:i\s+(?:have|made)\s+a\s+plan|i\s+have\s+the\s+means|i\s+can't\s+keep\s+myself\s+safe|i\s+cannot\s+keep\s+myself\s+safe|immediate\s+danger)\b", re.I),
    re.compile(r"\b(?:i\s+(?:overdosed|have\s+overdosed|took\s+an\s+overdose|have\s+hurt\s+myself|have\s+harmed\s+myself))\b", re.I),
)
_AMBER_PATTERNS = (
    re.compile(r"\b(?:suicid(?:e|al|ality)|self[- ]?harm|want\s+to\s+die|wish\s+i\s+were\s+dead|don't\s+want\s+to\s+live|do\s+not\s+want\s+to\s+live)\b", re.I),
    re.compile(r"\b(?:someone|they|he|she|my\s+(?:friend|partner|parent|child|family))\s+(?:is|may\s+be|might\s+be)\s+(?:suicidal|at\s+risk|in\s+danger|thinking\s+about\s+suicide|thinking\s+about\s+killing\s+themselves)\b", re.I),
    re.compile(r"\b(?:acute\s+crisis|crisis\s+intervention|cannot\s+stay\s+safe|can't\s+stay\s+safe)\b", re.I),
)

def classify_safety(query: str) -> str | None:
    text = " ".join(str(query or "").strip().casefold().split())
    if not text:
        return None
    if any(pattern.search(text) for pattern in _RED_PATTERNS):
        return "red"
    if any(pattern.search(text) for pattern in _AMBER_PATTERNS):
        return "amber"
    return None

def build_safety_contribution(*, request_id: str, query: str, safety_state: str, country: str = "") -> Mapping[str, Any]:
    state = str(safety_state or "amber").strip().casefold()
    if state not in {"red", "amber"}:
        state = "amber"
    if state == "red":
        response = (
            "I’m glad you said it plainly. You do not have to carry this alone. "
            "If you may act on this now, call your local emergency services or go "
            "to the nearest emergency department. If you can, stay with another "
            "person and move away from anything you could use to hurt yourself."
        )
    else:
        response = (
            "If this is about you or someone else and there is any chance of "
            "self-harm soon, please bring another person into the situation now. "
            "If there is immediate danger, call local emergency services or go "
            "to the nearest emergency department."
        )
    return {
        "contract_version": "v1",
        "request_id": str(request_id),
        "specialist_id": "safety",
        "status": "CONTRIBUTION",
        "voice_policy": "preserve_safety_utility_voice",
        "canonical_candidates": [],
        "boundary_notes": {
            "utility_version": SAFETY_UTILITY_VERSION,
            "sitewide": True,
            "priority": "highest",
            "bypasses_hrn": True,
            "bypasses_llm": True,
            "bypasses_retrieval": True,
        },
        "safety_flags": {
            "safety": True,
            "safety_interrupt": True,
            "safety_state": state,
            "country": str(country or "").strip(),
        },
        "payload": {
            "human_response": response,
            "safety_interrupt": True,
            "safety_state": state,
            "display_mode": "sitewide_safety",
            "country": str(country or "").strip(),
            "resources": {
                "emergency": {
                    "label": "Local emergency services / nearest emergency department",
                    "action": "emergency",
                },
                "verified_helplines": {
                    "label": "Find A Helpline — verified crisis support",
                    "url": "https://findahelpline.com/topics/suicidal-thoughts",
                    "action": "helpline",
                },
            },
            "next_movement": "Get a human being physically or by phone into the situation now.",
        },
    }

def safety_utility_snapshot() -> dict[str, Any]:
    return {
        "utility_version": SAFETY_UTILITY_VERSION,
        "specialist_id": "safety",
        "scope": "sitewide",
        "priority": "highest",
        "routing": "deterministic_pre_routing",
        "llm": False,
        "retrieval": False,
        "hrn_dependency": False,
    }
