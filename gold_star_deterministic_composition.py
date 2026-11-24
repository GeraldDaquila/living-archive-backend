"""Deterministic rendering of explicitly eligible Gold Star reasoning disciplines.

This module does not execute lesson prose as instructions and never transfers
exemplar answers or doorways. A small, reviewed plan registry maps approved
reasoning families to deterministic response structures. Unknown families or
changed lesson metadata fail closed.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


_PLANS = {
    "ethical_tradeoff_and_conflicting_harms": {
        "plan_id": "ethical_tradeoff_v1",
        "discipline_terms": (
            "competing claims", "power", "irreversible harms",
            "defensible criteria", "acknowledge sacrifice", "burdens",
        ),
        "boundary_terms": ("false consensus", "conceal sacrifice", "least power"),
        "response": (
            "A defensible choice begins by making the competing interests and possible losses visible. "
            "Identify what each person or group is trying to protect, compare the seriousness and "
            "reversibility of the harms, and examine who has influence over the decision.\n\n"
            "Use criteria that can be explained and challenged, include those most affected, and make "
            "unavoidable sacrifice explicit. Check whether the burdens fall disproportionately on people "
            "with the least power. A fair process does not require false consensus or promise a cost-free "
            "outcome; where important facts remain uncertain, keep the decision open to review."
        ),
    },
    "stakeholder_tradeoffs": {
        "plan_id": "stakeholder_tradeoffs_v1",
        "discipline_terms": (
            "obligations", "rights", "burdens", "power asymmetries", "trade-offs", "review",
        ),
        "boundary_terms": ("equal consideration", "equal outcomes"),
        "response": (
            "When obligations to different stakeholders conflict, first identify each party's legitimate "
            "rights, responsibilities, and exposure to the decision. Then compare who benefits, who bears "
            "the costs or risks, and who has the practical power to shape the available options.\n\n"
            "Give affected people a meaningful opportunity to be heard, make the reasons for the decision "
            "visible, and assign responsibility for its consequences. Fair consideration does not always "
            "mean identical outcomes: differences in role, impact, and capacity may justify different "
            "arrangements. Record the trade-offs and provide a way to review and correct the decision."
        ),
    },
}


def compose_deterministic_gold_star_response(
    query: str,
    contribution: Any,
) -> Optional[Dict[str, Any]]:
    """Render only a supported, eligible lesson through its reviewed plan."""
    if not isinstance(contribution, dict):
        return None
    if contribution.get("authority_mode") != "deterministic_structural_guidance_only":
        return None
    benchmark_id = str(contribution.get("benchmark_id") or "").strip()
    family = str(contribution.get("reasoning_family") or "").strip()
    discipline = str(contribution.get("discipline") or "").casefold()
    boundary = str(contribution.get("abstention_boundary") or "").casefold()
    if not benchmark_id or not str(query or "").strip():
        return None
    plan = _PLANS.get(family)
    if plan is None:
        return None
    if not all(term in discipline for term in plan["discipline_terms"]):
        return None
    if not all(term in boundary for term in plan["boundary_terms"]):
        return None
    return {
        "response": plan["response"],
        "benchmark_id": benchmark_id,
        "reasoning_family": family,
        "plan_id": plan["plan_id"],
        "application_evidence_spans": [
            span for span in plan["response"].split("\n\n") if span.strip()
        ],
        "abstention_boundary_applied": True,
    }
