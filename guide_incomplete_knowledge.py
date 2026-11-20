"""Reusable Guide reasoning contract for stewardship under incomplete knowledge.

The module recognizes a bounded decision task and supplies task-specific
composition requirements. It does not make the decision, infer facts, or
select a doorway.
"""
from __future__ import annotations

import re
from typing import Any

VERSION = "1.1"

_STEWARD = re.compile(r"\b(?:steward|stewardship|custodian|custodianship)\b", re.I)
_UNCERTAINTY = re.compile(
    r"\b(?:incomplete knowledge|uncertain(?:ty)?|don't know|do not know|"
    r"unknowns?|limited information|insufficient information|ambiguous evidence|"
    r"acting without (?:all|complete) the facts|not enough evidence)\b",
    re.I,
)
_ACTION = re.compile(
    r"\b(?:how should|what should|how can|what can|act|acting|decide|decision|"
    r"respond|proceed|choose|navigate|manage)\b",
    re.I,
)

_ARCHITECTURAL_CONTRACT = """STEWARDSHIP UNDER INCOMPLETE KNOWLEDGE — SHARED REASONING DISCIPLINE:
When a question concerns stewardship or accountable action under material uncertainty, make the epistemic state legible before recommending action. Distinguish (a) directly known facts, including what is directly observed or otherwise established, (b) interpretations and inferences, (c) assumptions being relied upon, (d) material unknowns, and (e) whose situated knowledge or perspective is absent. State confidence in proportion to evidence; do not disguise uncertainty with fluent prose, invent precision, or manufacture consensus. Identify what evidence would materially change the assessment.

Then calibrate action to the actual decision: stakes, urgency, who may be affected, the steward's legitimate authority and capacity, and how reversible the choice really is. Separate safe, useful actions that can be taken now from questions that need verification, consultation, testing, expertise, escalation, or a pause before commitment. Prefer proportionate, low-regret steps that preserve options only when delay is safe; reversibility is not a substitute for consent, legitimacy, or harm assessment. When delay itself creates serious or imminent harm, take the least harmful protective action within legitimate authority, explain the uncertainty, and seek review as soon as feasible.

Treat affected people's situated knowledge as evidence, not ceremonial consultation. Make visible who receives benefits, bears burdens and risks, and holds decision power. For high-consequence, irreversible, or out-of-authority decisions, use safeguards, affected-party input, relevant expertise, and escalation; do not imply that consultation alone transfers accountability. AI and other tools may organize evidence, surface alternatives, and test assumptions; they do not acquire human or institutional decision authority.

A decision made under incomplete knowledge must remain correctable. Name observable signals to monitor, the person or body accountable for monitoring, a review point or trigger where the decision will be reviewed, and what evidence would warrant continuation, adaptation, reversal, or stopping. Preserve material assumptions and reasons so later learning can identify and correct error. This discipline is task-dependent, not a mandatory checklist for unrelated questions."""

_QUERY_CONTRACT = """QUERY-LEVEL REQUIREMENTS — GIVE A PRACTICAL METHOD FOR ACTING UNDER UNCERTAINTY:
Answer the visitor's question directly and make the method usable without turning it into a long checklist. The response must make four things unmistakable:
1. WHAT IS KNOWN AND NOT KNOWN: separate established facts from inference, assumptions, unknowns, and missing perspectives; indicate where confidence is limited and what evidence or voice could change the picture.
2. WHAT THE SITUATION ALLOWS NOW — what can safely be done now: assess stakes, urgency, affected people, legitimate authority, capacity, and reversibility. Distinguish safe immediate steps from actions that require checking, consultation, expertise, safeguards, escalation, or deferral.
3. HOW TO ACT PROPORTIONATELY: recommend a next step that fits the evidence and stakes, preserves options where appropriate, and does not shift costs or risks invisibly onto others. State when waiting is unsafe and a least-harm protective action is warranted.
4. HOW TO REMAIN CORRECTABLE: identify what to monitor, who is accountable, when or on what signal to review, and what would trigger continuing, adapting, reversing, or stopping the decision.

Do not merely say “gather more information,” “consider the consequences,” or “remain accountable”; specify what to examine and how it changes the next action. Do not imply complete knowledge is attainable, every decision can wait, reversibility alone makes an action safe, or AI can own the decision. Keep the answer concise and natural; use the smallest structure that makes these distinctions clear. Retain any independently verified, directly relevant canonical doorway selected by the normal doorway process."""

def build_incomplete_knowledge_plan(query: str) -> dict[str, Any] | None:
    """Return the shared and query-level reasoning contract for matching tasks."""
    raw = re.sub(r"\s+", " ", str(query or "")).strip()
    if not raw:
        return None
    if not (_STEWARD.search(raw) and _UNCERTAINTY.search(raw) and _ACTION.search(raw)):
        return None
    return {
        "version": VERSION,
        "task_class": "stewardship_under_incomplete_knowledge",
        "architectural_contract": _ARCHITECTURAL_CONTRACT,
        "composition_instruction": _QUERY_CONTRACT,
        "required_dimensions": [
            "known_inferred_assumed_unknown",
            "confidence_and_missing_perspectives",
            "stakes_urgency_authority_and_reversibility",
            "proportionate_action_and_safeguards",
            "feedback_review_and_revision_conditions",
            "human_accountability_and_ai_boundary",
        ],
    }

__all__ = ["VERSION", "build_incomplete_knowledge_plan"]
