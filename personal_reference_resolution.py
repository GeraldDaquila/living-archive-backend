"""Shared detection and safe resolution policy for personal-reference questions."""
from __future__ import annotations
import re
PERSONAL_REFERENCE_VERSION = "1.0"
_PERSONAL_ARTIFACT = (
    r"(?:protocol|framework|approach|method|practice|principle|position|"
    r"decision|agreement|standard|rule|criteria|plan|commitment|teaching|"
    r"belief|view|preference|instruction|understanding)"
)
_PERSONAL_REFERENCE_PATTERNS = (
    rf"\b(?:my|our|the one we|what we)\b.{{0,100}}\b{_PERSONAL_ARTIFACT}\b",
    r"\bwhat (?:did i|have i|did we|have we) (?:say|decide|agree|establish|settle|define)",
    r"\bwhat was (?:my|our) (?:position|decision|agreement|approach|protocol|framework)",
    r"\b(?:as i said|as we agreed|what i previously said|what we previously agreed)\b",
)
def is_personal_reference_question(query: str) -> bool:
    """Detection is a routing hint, never proof that a personal item exists."""
    text = re.sub(r"\s+", " ", str(query or "")).strip()
    return bool(text) and any(re.search(p, text, re.I) for p in _PERSONAL_REFERENCE_PATTERNS)
def personal_reference_fallback(query: str) -> str:
    """Honest deterministic response when no verified personal source is available."""
    return (
        "I can help recover your protocol, but I can't verify its exact wording or steps "
        "from the conversation and source material available to this response. I won't "
        "replace your established position with a protocol I invent.\n\n"
        "The right next step is to locate the teaching or source that prompted the conflict "
        "and compare it with the protocol you established. If you share the teaching, or "
        "where your protocol was recorded, I can help recover the actual steps and keep "
        "your original distinctions intact. If you meant to formulate a new protocol "
        "rather than retrieve an existing one, I can help do that separately."
    )
