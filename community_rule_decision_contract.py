"""Shared runtime and evaluation contract for community liberty-limit decisions.

This module keeps visitor composition and held-out evaluation on one set of
observable requirements. Every required dimension must be present; majority
preference alone is not sufficient.
"""
from __future__ import annotations

import re
from typing import Any

_VERSION = "1.0"

_PURPOSE = (
    "shared purpose", "shared need", "shared obligations", "coordination problem",
    "coordination need", "demonstrable harm", "actual harm", "common need", "shared goal",
)
_PROPORTIONALITY = (
    "proportionate", "proportionality", "necessary", "least restrictive",
    "least-restrictive",
)
_BURDEN = (
    "who benefits", "who bears", "who carries", "fairly distributed", "fair burden",
    "fair burden allocation", "bears burdens fairly", "burdens fairly", "burden fairly",
    "does not disproportionately fall", "not disproportionately borne",
    "costs and benefits", "benefits and costs",
)
_ACCOMMODATION = (
    "accommodation", "accommodated", "reasonable accommodation",
    "accommodate different needs", "accommodate if possible",
    "accommodate where possible", "reasonable adjustments",
    "adjustments where needed", "adjustment for disability", "individual adjustment",
)
_PARTICIPATION = (
    "people most affected should have a meaningful opportunity to shape",
    "affected people should have a meaningful opportunity to shape",
    "those affected should have a meaningful opportunity to shape",
    "affected people's participation in shaping",
    "affected people’s participation in shaping",
    "shaped by the people most affected", "shaped by people most affected",
    "shaped by those most affected", "shaped by affected people",
    "people affected participate in shaping",
    "participation of affected people in shaping",
    "participation by affected people in shaping",
    "meaningful participation from those affected",
    "meaningful participation by affected",
    "meaningful participation in designing", "shape the decision", "shape the rule",
    "participate in setting the rule", "participate in designing the rule",
    "participate in shaping the rule", "include affected people in designing",
    "include those affected in shaping", "input from those affected before",
    "solicit input from those whose liberty would be curtailed",
)
_APPEAL_REVIEW = (
    "appeal", "question the rule", "challenge its application", "review point",
    "review the rule", "observable criteria",
)


def is_community_rule_decision_question(query: str) -> bool:
    low = " ".join(str(query or "").casefold().split())
    has_liberty = any(term in low for term in (
        "personal liberty", "individual freedom", "civil liberty",
    ))
    has_limit = any(term in low for term in (
        "limit", "restrict", "restriction", "rule",
    ))
    has_community = any(term in low for term in (
        "community", "shared obligation", "collective obligation", "shared risk",
    ))
    return has_liberty and has_limit and has_community


def _majority_only(text: str) -> bool:
    return bool(
        re.search(
            r"\bmajority\b.{0,40}\b(?:can|may|should|is entitled to|has the right to)\b.{0,80}\b(?:restrict|limit|control)\b",
            text,
        )
        or any(phrase in text for phrase in (
            "majority preference is enough",
            "majority alone justifies",
            "collective convenience alone justifies",
        ))
    )


def evaluate_community_rule_response(query: str, response: str) -> dict[str, Any]:
    """Return the same six-part evidence check for runtime and live evaluation."""
    applies = is_community_rule_decision_question(query)
    if not applies:
        return {"version": _VERSION, "applies": False, "passed": True, "checks": {}, "missing": []}
    low = " ".join(str(response or "").casefold().split())
    checks = {
        "legitimate_shared_purpose": any(term in low for term in _PURPOSE),
        "necessity_and_least_restrictive_means": any(term in low for term in _PROPORTIONALITY),
        "fair_burden_allocation": any(term in low for term in _BURDEN),
        "reasonable_accommodation": any(term in low for term in _ACCOMMODATION),
        "affected_party_participation": any(term in low for term in _PARTICIPATION),
        "appeal_and_review": any(term in low for term in _APPEAL_REVIEW),
    }
    majority_only = _majority_only(low)
    missing = [name for name, passed in checks.items() if not passed]
    if majority_only:
        missing.append("majority_preference_not_sufficient")
    return {
        "version": _VERSION,
        "applies": True,
        "passed": not missing,
        "checks": checks,
        "majority_only": majority_only,
        "missing": missing,
    }


def build_community_rule_decision_instruction() -> str:
    return (
        "COMMUNITY RULES THAT LIMIT PERSONAL LIBERTY: Name the legitimate shared purpose and "
        "specific harm; test necessity, proportionality, and the least restrictive workable means; "
        "make clear who benefits and who bears the costs; explicitly address reasonable accommodation; "
        "explain how people most affected can meaningfully shape the rule; and provide an appeal route "
        "plus observable review criteria. These are separate evidence dimensions: do not leave any "
        "dimension implicit or treat a generic statement about fairness as a substitute for burden "
        "allocation or affected-party participation. Integrate all dimensions in coherent, natural "
        "prose rather than a mechanical checklist. Majority preference is not proof."
    )
