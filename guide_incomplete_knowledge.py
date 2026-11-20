"""Reusable Guide reasoning contract for stewardship under incomplete knowledge.

The module recognizes a bounded decision task and supplies task-specific
composition requirements. It does not make the decision, infer facts, or
select a doorway.
"""
from __future__ import annotations

import re
from typing import Any

VERSION = "1.0"

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
When a question concerns stewardship or accountable action under material uncertainty, do not treat uncertainty as either a reason for paralysis or permission to guess. Make the epistemic state legible: distinguish what is directly known, what is inferred, what is assumed, what remains unknown, and whose knowledge or experience is missing. Calibrate confidence to the evidence; do not manufacture precision or collapse disagreement into consensus.

Match action to stakes, urgency, reversibility, and the steward's actual authority and capacity. Prefer proportionate, low-regret, reversible steps that preserve options while learning when delay is safe. Where a decision is high-consequence, difficult to reverse, outside the steward's competence or authority, or exposes others to serious harm, seek affected-party input and appropriate expertise, add safeguards, escalate, or defer the irreversible commitment when feasible. Where delay itself creates serious or imminent harm, take the least harmful protective action within legitimate authority and explain the uncertainty.

Treat affected people's situated knowledge as evidence, not as a ceremonial consultation. Make the distribution of benefits, burdens, risks, and decision power visible. AI and other tools may organize evidence, surface alternatives, and test assumptions; they do not acquire the authority or accountability of the human or institution responsible for the decision.

A responsible decision remains provisional where evidence is provisional. Specify what will be monitored, who is accountable for monitoring it, when or under what signal the decision will be reviewed, and what evidence would trigger continuation, adaptation, reversal, or stopping. Preserve a record of material assumptions and reasons so later learning can correct the decision. This is a task-dependent discipline, not a mandatory checklist for unrelated questions."""

_QUERY_CONTRACT = """QUERY-LEVEL REQUIREMENTS — ANSWER HOW TO ACT, NOT ONLY HOW TO THINK:
Answer the practical question directly. Give the visitor a usable sequence: (1) map known facts, inferences, assumptions, unknowns, and missing perspectives; (2) identify the decision's stakes, urgency, affected people, authority, and reversibility; (3) distinguish what can safely be done now from what should be tested, deferred, or escalated; (4) choose a proportionate step that preserves options where possible and add safeguards where consequences may be serious; and (5) name observable signals, a review point, the accountable person, and conditions for changing or stopping course. Explain that urgent protective action may still be necessary when waiting is itself dangerous. Do not imply that complete knowledge is attainable, that every decision can be delayed, or that reversibility alone makes an action safe. Do not transfer decision authority to AI. Keep the answer concise enough to use, and retain any independently verified, directly relevant canonical doorway selected by the normal doorway process."""

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
