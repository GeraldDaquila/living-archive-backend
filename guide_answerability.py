"""Layered answerability: answer general concepts without inventing authority.

This contract separates ordinary conceptual answerability from source-specific
authority. It does not certify facts, establish institutional doctrine, or
override higher-stakes verification and safety requirements.
"""
from __future__ import annotations

import re
from typing import Any

VERSION = "1.0"

_REALITY_IDEOLOGY = re.compile(
    r"\b(?:lead|leading|leadership)\b.{0,100}\b(?:from|grounded in|guided by)\b.{0,40}\breality\b"
    r".{0,70}\b(?:rather than|instead of|over|vs\.?|versus|not)\b.{0,50}\bideolog\w*\b"
    r"|\b(?:reality[- ]led|reality[- ]based)\b.{0,70}\b(?:ideolog\w*|doctrine)\b"
    r"|\b(?:ideolog\w*|doctrine)\b.{0,70}\b(?:reality[- ]led|reality[- ]based)\b",
    re.I,
)
_MEANING_REQUEST = re.compile(
    r"\b(?:what does|what do|what is|how is|how do|how does|explain|meaning of|"
    r"what would it mean|what is meant by)\b",
    re.I,
)

_SOURCE_SPECIFIC_OR_SOURCE_ONLY = re.compile(
    r"\b(?:according to|as defined by|official|formal|institution(?:al)?[- ]specific|"
    r"the archive(?:'s)? definition|in the living archive(?:'s)? (?:own )?(?:terms|usage|framework))\b"
    r"|\b(?:using|based on|drawn from)\b.{0,35}\b(?:only|solely|exclusively)\b.{0,30}\b(?:source|document|archive|text|publication)\b"
    r"|\b(?:only|solely|exclusively)\b.{0,35}\b(?:source|document|archive|text|publication)\b",
    re.I,
)
_HIGH_STAKES_CONTEXT = re.compile(
    r"\b(?:medical|clinical|healthcare|diagnos\w*|treatment plan|medication|legal|law|lawsuit|"
    r"investment|financial|tax|emergency|safety-critical|self[- ]harm)\b",
    re.I,
)

ARCHITECTURAL_CONTRACT = """LAYERED ANSWERABILITY — SHARED REASONING DISCIPLINE:
Do not treat the absence of an authoritative, source-specific definition as proof that a question is unanswerable. Separate answerability from authority. First determine what can responsibly be explained from established general knowledge and ordinary conceptual usage; distinguish that from interpretation or inference; and distinguish both from claims about what a particular institution formally teaches, defines, or endorses. Answer the answerable portion directly. Qualify interpretations in proportion to their support. Attribute institutional doctrine only when an available authoritative source supports that attribution. If source-specific authority is unavailable, state that limitation narrowly rather than withholding the general explanation. Abstain only from the portion that cannot responsibly be answered; do not manufacture certainty, and do not manufacture uncertainty to avoid useful reasoning. This discipline does not override safety, high-stakes professional boundaries, explicit source-only constraints, or the need to verify time-sensitive and specific factual claims."""

QUERY_CONTRACT = """QUERY-LEVEL REQUIREMENTS — EXPLAIN LEADING FROM REALITY RATHER THAN IDEOLOGY:
Answer the general conceptual question directly; do not require a formal Living Archive definition before explaining ordinary meaning. Explain that leading from reality begins with actual conditions, observable evidence, constraints, and the lived experience of affected people, and allows understanding and action to be revised when evidence warrants it. Contrast this with allowing a fixed set of beliefs, doctrine, or a predetermined preferred outcome to dictate which facts are noticed, how contrary evidence is interpreted, or what conclusions are permitted. Preserve the important boundary: reality-led leadership is not value-free or principle-free; values can guide what matters, while evidence and consequences test whether one's understanding and chosen means fit the world as it is. Give one concrete practical example. Clearly label this as a general conceptual explanation, not a formal Living Archive definition, unless a retrieved authoritative Archive source establishes such a definition. Do not claim that all ideology is inherently false or harmful."""

def is_reality_vs_ideology_leadership_question(query: str) -> bool:
    """Recognize the bounded conceptual contrast and common paraphrases."""
    q = re.sub(r"\s+", " ", str(query or "")).strip()
    return bool(
        q
        and _REALITY_IDEOLOGY.search(q)
        and _MEANING_REQUEST.search(q)
        and not _SOURCE_SPECIFIC_OR_SOURCE_ONLY.search(q)
        and not _HIGH_STAKES_CONTEXT.search(q)
    )

def build_answerability_plan(query: str) -> dict[str, Any] | None:
    """Return architectural and query-level guidance for this answerable concept."""
    if not is_reality_vs_ideology_leadership_question(query):
        return None
    return {
        "version": VERSION,
        "task_class": "reality_vs_ideology_leadership",
        "architectural_contract": ARCHITECTURAL_CONTRACT,
        "composition_instruction": QUERY_CONTRACT,
        "required_dimensions": [
            "actual_conditions_and_evidence",
            "fixed_belief_or_preferred_outcome_contrast",
            "values_are_not_excluded",
            "revision_in_response_to_evidence",
            "general_meaning_distinguished_from_institutional_doctrine",
        ],
    }

def reality_vs_ideology_recovery() -> str:
    """Provide a bounded, source-independent explanation of the concept."""
    return (
        "To lead from reality rather than ideology is to let actual conditions, evidence, "
        "constraints, and people's lived experience shape how you understand a situation and what you do. "
        "Ideology becomes the driver when a fixed set of beliefs or a preferred outcome decides in advance "
        "which facts count, which evidence is noticed, and which conclusions are allowed.\n\n"
        "This does not mean leading without values or principles. Values can guide what matters; reality tests "
        "whether our understanding and chosen means fit the world as it is. A reality-led leader states "
        "assumptions, listens to people affected, looks for evidence that could challenge the current view, "
        "and changes course when the facts warrant it. Ideological rigidity instead protects the doctrine "
        "by dismissing or explaining away contrary evidence.\n\n"
        "For example, if a policy intended to improve public services is not helping the people it was designed "
        "for, reality-led leadership examines the results, listens to those affected, and revises the policy. "
        "Ideological rigidity insists the policy must be working and discounts the evidence. This is a general "
        "conceptual explanation, not a claim about a formal Living Archive definition."
    )

def has_reality_vs_ideology_explanation(response: str) -> bool:
    """Require the central contrast, value boundary, and evidence-responsive action."""
    text = re.sub(r"\s+", " ", str(response or "")).casefold()
    return bool(
        re.search(r"\breality\b.{0,220}\b(?:evidence|actual conditions|observable conditions)\b", text)
        and re.search(r"\bideolog\w*\b.{0,240}\b(?:belief|doctrine|preferred outcome|predetermined)\b", text)
        and re.search(r"\b(?:values|principles)\b.{0,180}\b(?:reality|evidence|conditions|guide)\b", text)
        and re.search(r"\b(?:change|revise|adapt|correct)\w*\b.{0,180}\b(?:evidence|facts|conditions)\b|\b(?:evidence|facts|conditions)\b.{0,180}\b(?:change|revise|adapt|correct)\w*\b", text)
        and re.search(r"\b(?:for example|imagine|suppose|in practice)\b", text)
    )


def is_unjustified_conceptual_abstention(query: str, response: str) -> bool:
    """Detect a generic evidence-limit refusal to an ordinary conceptual question.

    This is a response-quality signal, not a claim that every concept is
    answerable. Source-only requests and high-stakes questions are excluded.
    The caller gets one bounded provider repair attempt; this function never
    manufactures subject-matter content.
    """
    q = re.sub(r"\\s+", " ", str(query or "")).strip()
    answer = re.sub(r"\\s+", " ", str(response or "")).strip()
    if not q or len(answer) < 20:
        return False
    if _SOURCE_SPECIFIC_OR_SOURCE_ONLY.search(q) or _HIGH_STAKES_CONTEXT.search(q):
        return False
    if not _MEANING_REQUEST.search(q):
        return False
    if not re.search(
        r"\\b(?:role|purpose|significance|importance|function|value|meaning|"
        r"relationship|contribution|impact|effect|nature|concept|principle)\\b",
        q,
        re.I,
    ):
        return False
    return bool(re.search(
        r"(?:\\b(?:i|we)\\s+(?:cannot|can't|can not|am unable to)\\b.{0,100}"
        r"(?:define|explain|establish|determine|answer|identify)|"
        r"\\bnot enough (?:information|evidence|context)\\b.{0,100}"
        r"(?:reliab|available|response|answer)|"
        r"\\binformation available in this response alone\\b|"
        r"\\bcannot (?:reliably )?(?:define|explain|answer)\\b)",
        answer,
        re.I,
    ))
