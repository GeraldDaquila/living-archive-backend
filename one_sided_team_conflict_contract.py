"""Scoped reasoning contract for one-sided accounts of multi-party team conflict."""
from __future__ import annotations

import re
from typing import Any

VERSION = "1.0"

_CONFLICT = re.compile(
    r"\b(?:team|workplace|colleague|coworker|co-worker|manager|supervisor|"
    r"employee|staff|organizational|organisation|organization)\b", re.I
)
_DISPUTE = re.compile(
    r"\b(?:conflict|disagreement|dispute|tension|clash|friction|falling out|"
    r"apply.{0,35}(?:archive|framework|idea|concept|principle))\b", re.I
)
_ONE_SIDED = re.compile(
    r"\b(?:one[- ]sided|one person'?s account|only one (?:person|side|party)|"
    r"single (?:account|narrative|perspective)|other party'?s perspective|"
    r"both sides|before offering a frame|before applying)\b", re.I
)

def is_one_sided_team_conflict_question(question: str) -> bool:
    """Match multi-party team conflict with explicit partial-account/context cues."""
    q = " ".join(str(question or "").split())
    return bool(len(q) >= 24 and _CONFLICT.search(q) and _DISPUTE.search(q) and _ONE_SIDED.search(q))


def build_one_sided_team_conflict_instruction(question: str) -> str:
    if not is_one_sided_team_conflict_question(question):
        return ""
    return (
        "ONE-SIDED ACCOUNT OF A MULTI-PARTY TEAM CONFLICT — CONTEXT BEFORE FRAMING: "
        "Take the visitor's experience seriously without treating one account as the complete record. "
        "Distinguish observable events, direct evidence or quotations, reported information, interpretations "
        "and unknowns; do not infer the absent party's motives or invent their perspective. Establish relevant "
        "roles, authority, dependencies, history, prior agreements, formal policies and decision rights. "
        "Before recommending direct dialogue or seeking another account, consider whether doing so is safe "
        "and appropriate; attend proportionately to coercion, harassment, discrimination, threats, retaliation "
        "risk and serious power asymmetry. Do not force false equivalence or require a visitor to confront "
        "someone where that may be unsafe; a confidential, facilitated or formal channel may be more suitable. "
        "Clarify whether the visitor seeks understanding, repair, a boundary, a decision or accountability. "
        "Offer one manageable next question rather than a burdensome intake list. Apply an Archive frame only "
        "after enough context is established, explain why it fits, and preserve uncertainty. Do not let a "
        "retrieved doorway validate the visitor's account; keep navigation separate and omit an unverified or "
        "irrelevant doorway. This contract applies only to the qualifying multi-party conflict inquiry."
    )


def evaluate_one_sided_team_conflict_response(question: str, response: str) -> dict[str, Any]:
    applies = is_one_sided_team_conflict_question(question)
    if not applies:
        return {"applies": False, "passed": True, "missing": []}
    text = " ".join(str(response or "").casefold().split())
    groups = {
        "partial_account_without_dismissal": r"\b(?:one account|one person's account|partial perspective|not the whole|not the complete record|single account)\b",
        "facts_vs_interpretation": r"\b(?:observed|observation|what happened|interpretation|inferred|infer|unknown|intent)\b",
        "role_or_power_context": r"\b(?:role|authority|power|dependen|decision rights|governance)\b",
        "safety_before_dialogue": r"\b(?:safe|safety|retaliat|coerc|harass|facilitat|formal channel)\b",
        "outcome_clarification": r"\b(?:repair|understanding|boundary|accountability|outcome|decision)\b",
        "one_next_question": r"\?",
    }
    missing = [name for name, pattern in groups.items() if not re.search(pattern, text)]
    # Reject premature adjudication or mandatory direct confrontation.
    if re.search(r"\b(?:the other person is|they are clearly|they obviously|you should confront|must confront)\b", text):
        missing.append("no_premature_adjudication_or_forced_confrontation")
    return {"applies": True, "passed": not missing, "missing": missing}


def recover_one_sided_team_conflict_response() -> str:
    return (
        "Before applying an Archive idea, I would treat this as one person's account of a shared situation—not "
        "as the whole record, while still taking that person's experience seriously. First, separate what "
        "happened from what each person thinks it means: what was said or done, what was directly observed, "
        "what is inferred about intent, and what remains unknown. Then establish the relationship and decision "
        "context: each person's role and authority, any dependency or power difference, relevant history, prior "
        "agreements, and applicable team policies or governance arrangements. It is also important to consider "
        "whether direct dialogue or seeking the other person's account is safe and appropriate; where there is "
        "coercion, harassment, retaliation risk, or a serious power imbalance, a confidential, facilitated, or "
        "formal channel may be safer. Finally, clarify what is needed now—understanding, repair, a boundary, a "
        "decision, or accountability—before choosing a frame. We can start with one question: **What happened, "
        "in concrete terms, and which parts of your account are direct observations versus interpretations of "
        "the other person's intentions?**"
    )


__all__ = [
    "VERSION",
    "is_one_sided_team_conflict_question",
    "build_one_sided_team_conflict_instruction",
    "evaluate_one_sided_team_conflict_response",
    "recover_one_sided_team_conflict_response",
]
