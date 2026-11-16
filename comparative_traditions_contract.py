"""Final-boundary protection for comparative spiritual-tradition inquiries.

This contract prevents an institutional decision template from displacing a
visitor's request for comparative understanding. It does not rank traditions
or make tradition-specific factual claims. It may return one narrowly approved
public Archive continuation when the visitor's question clearly fits it.
"""
from __future__ import annotations

import re


_TRADITION_TERMS = re.compile(
    r"\b(?:spiritual|religious|religion|religions|faith|faiths|theological|"
    r"philosophical|contemplative|indigenous|buddhis(?:m|t)|christianity|"
    r"christian|islam|muslim|hinduism|hindu|judaism|jewish|sikhism|sikh|"
    r"taoism|daoism|shinto|jainism|zoroastrianism)\b", re.I
)
_PLURAL_TERMS = re.compile(
    r"\b(?:multiple|different|various|comparative|between|across|traditions?|"
    r"similarities|differences|compare|comparison)\b", re.I
)
_APPROACH_TERMS = re.compile(
    r"\b(?:approach|understand|engage|compare|comparison|similarit(?:y|ies)|"
    r"differ(?:ence|ences)|contrast|study|learn|respect|intellectual discipline)\b", re.I
)
_DOMAIN_MARKERS = re.compile(
    r"\b(?:tradition|traditions|practitioners|sources|texts|history|historical|"
    r"context|contexts|claims|evidence|interpretation|interpretations|"
    r"differences|distinctions|beliefs|practices|experience|experiences|"
    r"epistemic|uncertainty|standpoint|criticism|critical|compare|comparison)\b", re.I
)
_INSTITUTIONAL_MARKERS = re.compile(
    r"\b(?:organisation|organization|governance|responsibilit(?:y|ies)|"
    r"consequences|costs|decision|decisions|accountability|institutional|"
    r"stakeholders|operating)\b", re.I
)


def is_comparative_traditions_question(question: str) -> bool:
    """Recognize questions about approaching or comparing plural traditions."""
    text = str(question or "").strip()
    return bool(
        text
        and _TRADITION_TERMS.search(text)
        and _PLURAL_TERMS.search(text)
        and _APPROACH_TERMS.search(text)
    )


def response_substitutes_institutional_frame(question: str, response: str) -> bool:
    """Detect a governance/decision answer that omits comparative substance."""
    if not is_comparative_traditions_question(question):
        return False
    text = str(response or "")
    domain_count = len(_DOMAIN_MARKERS.findall(text))
    institutional_count = len(_INSTITUTIONAL_MARKERS.findall(text))
    return institutional_count >= 3 and domain_count < 5


def recovery_response() -> str:
    """Return a bounded, general answer when the composer misses the inquiry."""
    return (
        "Multiple spiritual traditions can be approached with respect by first "
        "trying to understand each on its own terms. Attend to its history, "
        "language, practices, sources of authority, and the ways its practitioners "
        "describe their own experience. Respect does not require agreement, and "
        "understanding does not require suspending critical thought.\n\n"
        "Intellectual discipline begins by distinguishing kinds of claims. "
        "Historical claims call for historical evidence; philosophical claims "
        "call for careful examination of their reasoning; empirical claims call "
        "for appropriate evidence; and claims about spiritual experience call "
        "for attention to how that experience is described and interpreted "
        "within its tradition. Apply standards of clarity and fairness "
        "consistently without assuming that all traditions are saying the same "
        "thing or that they cannot be compared.\n\n"
        "A careful comparison therefore combines openness with discernment. "
        "Let each tradition speak in its own vocabulary, notice where its ideas "
        "genuinely differ, and be honest about what is established, what remains "
        "interpretive, and what cannot be independently verified. The aim is "
        "neither to rank traditions prematurely nor to erase their differences, "
        "but to learn without misrepresenting them."
    )


_VERIFIED_DOORWAY = {
    "title": "At the Edge of Explanation",
    "url": "https://geralddaquila.com/2026/07/20/at-the-edge-of-explanation/",
}


def verified_doorway(question: str) -> dict[str, str] | None:
    """Return the approved public continuation for plural-tradition inquiry.

    The destination is grounded in the published essay's explicit treatment of
    science, philosophy, spirituality, distinct ways of knowing, and the risk of
    reducing one domain to another. Keep the trigger bounded to this inquiry
    family; otherwise fail closed rather than attach a merely adjacent essay.
    """
    if not is_comparative_traditions_question(question):
        return None
    return dict(_VERIFIED_DOORWAY)
