"""Final-boundary protection and quality standard for comparative-traditions inquiries.
The contract preserves internal diversity, epistemic distinctions, and fair comparison.
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
_FLATTENING_MARKERS = re.compile(
    r"\b(?:all (?:three|four|five|six|these) (?:religions|faiths|traditions)|"
    r"all traditions (?:believe|teach|share)|they all (?:believe|teach|share)|"
    r"every religion (?:believes|teaches|shares)|"
    r"(?:a|the) (?:shared|common) focus on the afterlife)\b", re.I
)

def is_comparative_traditions_question(question: str) -> bool:
    text = str(question or "").strip()
    return bool(text and _TRADITION_TERMS.search(text)
                and _PLURAL_TERMS.search(text) and _APPROACH_TERMS.search(text))

def response_substitutes_institutional_frame(question: str, response: str) -> bool:
    if not is_comparative_traditions_question(question):
        return False
    text = str(response or "")
    return (len(_INSTITUTIONAL_MARKERS.findall(text)) >= 3
            and len(_DOMAIN_MARKERS.findall(text)) < 5)

def response_flattens_traditions(question: str, response: str) -> bool:
    if not is_comparative_traditions_question(question):
        return False
    return bool(_FLATTENING_MARKERS.search(str(response or "")))

def response_requires_quality_repair(question: str, response: str) -> bool:
    return (response_substitutes_institutional_frame(question, response)
            or response_flattens_traditions(question, response))

def recovery_response() -> str:
    return (
        "Begin by trying to understand each tradition on its own terms. Attend to "
        "its histories, sources, languages, practices, and the ways practitioners "
        "describe their own commitments and experiences. No single text, leader, "
        "or representative can stand for every community within a tradition; "
        "internal differences and changing historical contexts matter. Respect "
        "does not require agreement, and careful inquiry does not require "
        "suspending criticism.\n\n"
        "Then distinguish the kinds of claims being made. Historical claims call "
        "for historical evidence; philosophical and theological claims require "
        "careful attention to concepts and reasoning; empirical claims need "
        "evidence suited to what they assert; and accounts of spiritual experience "
        "need to be understood in their own interpretive and communal settings. "
        "Do not use one method as if it could settle every kind of question, and "
        "be clear about what is established, contested, interpreted, or not "
        "independently verifiable.\n\n"
        "Comparison can reveal genuine affinities, but similarity is not proof "
        "that traditions mean the same thing. Nor should differences be turned "
        "into caricatures or rankings. Let each tradition's own vocabulary and "
        "internal diversity remain visible, compare like with like where possible, "
        "and revise your account when practitioners, sources, or stronger evidence "
        "complicate it. The aim is understanding without appropriation, false "
        "equivalence, or premature judgment."
    )

_VERIFIED_DOORWAY = {
    "title": "At the Edge of Explanation",
    "url": "https://geralddaquila.com/2026/07/20/at-the-edge-of-explanation/",
}

def verified_doorway(question: str) -> dict[str, str] | None:
    if not is_comparative_traditions_question(question):
        return None
    return dict(_VERIFIED_DOORWAY)
