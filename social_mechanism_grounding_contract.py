"""Shared hard contract for concrete social-mechanism explanations.

A qualifying illustration must connect a real-world setting, a shared narrative or
symbolic form, an enacted communal practice, and a resulting collective effect.
The causal connection must be expressed in the same sentence as the practice and
effect; unrelated keywords elsewhere in the illustration cannot satisfy it.

This remains a conservative syntactic admission heuristic, not semantic certification.
Its reliability must still be assessed with adversarial tests and held-out visitor evaluation.
"""
from __future__ import annotations

import re

_VERSION = "1.1"

_SETTING_OR_ACTOR = re.compile(
    r"\b(?:community|communities|village|town|neighbourhood|neighborhood|"
    r"members|residents|families|citizens|people|workers|students|congregation|"
    r"team|association|nation|society)\b", re.I,
)
_SHARED_FORM = re.compile(
    r"\b(?:founding story|story|myth|narrative|flag|anthem|pledge|ritual|"
    r"ceremony|festival|memorial|monument|custom|tradition|symbol|song|"
    r"commemoration|public gathering)\b", re.I,
)
_ENACTED_PRACTICE = re.compile(
    r"\b(?:retell|repeat|recite|display|gather|meet|mark|celebrate|commemorate|"
    r"perform|enact|teach|pass down|renew|observe|carry|wear|sing|build|share)\w*\b",
    re.I,
)
_COLLECTIVE_EFFECT = re.compile(
    r"\b(?:coordinates?|organizes?|organises?|brings? together|reminds? .*?(?:belonging|identity|obligations?|commitment)|"
    r"turns? .*? into|makes? .*? part of .*?(?:identity|belonging|culture)|"
    r"makes? .*?(?:visible|public|expected|legitimate)|creates? a shared|"
    r"reinforces?|establishes?|signals?|defines?|"
    r"shapes? .*?(?:belonging|expectations|obligations|identity|authority)|"
    r"prompts?|mobilizes?|mobilises?|guides? .*?behavio?r|"
    r"sets? expectations|distributes? responsibilities|"
    r"people .*?(?:volunteer|cooperate|contribute|obey|participate|coordinate))\b",
    re.I,
)
_CAUSAL_LINK = re.compile(
    r"\b(?:so that|which means|thereby|as a result|because|when .*? then|"
    r"turns? .*? into|translates? .*? into|reminds? .*? that|teaches? .*? to)\b",
    re.I,
)


def requires_grounded_mechanism_example(question: str) -> bool:
    q = re.sub(r"\s+", " ", str(question or "")).strip().casefold()
    how = bool(re.search(r"\bhow\b", q))
    mechanism = bool(re.search(
        r"\b(?:organize|organise|shape|structure|coordinate|reinforce|reproduce|sustain|influence|"
        r"bind|unify|legitimate|regulate)\b", q
    ))
    collective = bool(re.search(
        r"\b(?:collective life|social life|community|communities|society|social order|"
        r"group identity|shared norms|culture|cultural life)\b", q
    ))
    symbolic_subject = bool(re.search(
        r"\b(?:myths?|symbols?|stories|narratives?|rituals?|traditions?|ceremonies|"
        r"shared memories|founding stories|sacred stories)\b", q
    ))
    return how and mechanism and collective and symbolic_subject


def has_grounded_mechanism_example(response: str) -> bool:
    text = re.sub(r"\s+", " ", str(response or "")).strip()
    marker = re.search(
        r"\b(?:for example|for instance|consider|imagine)\b\s*[:,]?\s*(.+)",
        text, re.I,
    )
    if not marker:
        return False

    # Keep proof local to the explicitly introduced illustration. Requiring all
    # mechanism elements and a causal connector in one sentence prevents a
    # decorative example from borrowing evidence from adjacent abstract prose.
    sentences = re.split(r"(?<=[.!?])\s+", marker.group(1))
    for sentence in sentences[:3]:
        if all(pattern.search(sentence) for pattern in (
            _SETTING_OR_ACTOR,
            _SHARED_FORM,
            _ENACTED_PRACTICE,
            _COLLECTIVE_EFFECT,
            _CAUSAL_LINK,
        )):
            return True
    return False
