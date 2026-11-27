"""Shared hard contract for concrete social-mechanism explanations.

A qualifying illustration must show a real-world setting, a shared narrative or
symbolic practice, what people do with it, and the resulting coordination,
expectation, identity, or authority effect. Merely naming a symbol and attaching
a generic verb is not demonstration.
"""
from __future__ import annotations

import re

_VERSION = "1.0"

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
    marker = re.search(r"\b(?:for example|for instance|consider|imagine)\b\s*[:,]?\s*(.+)", text, re.I)
    if not marker:
        return False
    # Keep the proof local: a later abstract paragraph cannot repair a decorative
    # example. Limit the illustration to its first three sentences.
    sentences = re.split(r"(?<=[.!?])\s+", marker.group(1))
    example = " ".join(sentences[:3]).casefold()
    setting_or_actor = bool(re.search(
        r"\b(?:community|communities|village|town|neighbourhood|neighborhood|"
        r"members|residents|families|citizens|people|workers|students|congregation|"
        r"team|association|nation|society)\b", example
    ))
    shared_form = bool(re.search(
        r"\b(?:founding story|story|myth|narrative|flag|anthem|pledge|ritual|"
        r"ceremony|festival|memorial|monument|custom|tradition|symbol|song|"
        r"commemoration|public gathering)\b", example
    ))
    enacted_practice = bool(re.search(
        r"\b(?:retell|repeat|recite|display|gather|meet|mark|celebrate|commemorate|"
        r"perform|enact|teach|pass down|renew|observe|carry|wear|sing|build|share)\w*\b",
        example
    ))
    collective_effect = bool(re.search(
        r"\b(?:coordinates?|organizes?|organises?|brings? together|reminds? .*?(?:belonging|identity|obligations?|commitment)|turns? .*? into|makes? .*? part of .*?(?:identity|belonging|culture)|"
        r"makes? .*?(?:visible|public|expected|legitimate)|"
        r"creates? a shared|reinforces?|establishes?|signals?|defines?|"
        r"shapes? .*?(?:belonging|expectations|obligations|identity|authority)|"
        r"prompts?|mobilizes?|mobilises?|guides? .*?behavio?r|"
        r"sets? expectations|distributes? responsibilities|"
        r"people .*?(?:volunteer|cooperate|contribute|obey|participate|coordinate))\b",
        example
    ))
    # Require a linked causal explanation, not four unrelated keyword mentions.
    causal_link = bool(re.search(
        r"\b(?:so that|which means|thereby|as a result|because|when .*? then|"
        r"turns? .*? into|translates? .*? into|reminds? .*? that|teaches? .*? to)\b",
        example
    ))
    return all((setting_or_actor, shared_form, enacted_practice, collective_effect, causal_link))
