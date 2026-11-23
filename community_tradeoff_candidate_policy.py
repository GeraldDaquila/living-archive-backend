"""Governed retrieval for community freedom/responsibility trade-offs.

This policy selects only existing runtime-transferable registry lessons.
It transfers reasoning discipline, never an exemplar answer or doorway.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

MAX_POLICY_CANDIDATES = 4

_CANDIDATES = (
    {
        "benchmark_id": "gs-2026-11-22-community-freedom-shared-responsibility-decision",
        "role": "core",
        "condition": "The question balances individual freedom with shared responsibility in a community decision.",
        "rationale": "Adds the newly approved, directly relevant discipline of rights protection, evidence, proportionality, fair burdens, and accountable review.",
    },
    {
        "benchmark_id": "gs-2026-11-23-community-rule-design-liberty-shared-obligations",
        "role": "conditional",
        "condition": "The question explicitly asks how to formulate, justify, or review a community rule, policy, or restriction.",
        "rationale": "Adds the more specific discipline for legitimate rule purpose, demonstrable need, least-restrictive means, reciprocal burdens, accommodation, appeal, and observable review.",
    },
    {
        "benchmark_id": "general-guide-ethical-tradeoff-2026-10",
        "role": "conditional",
        "condition": "The question explicitly identifies a trade-off, conflict, or competing obligations or interests.",
        "rationale": "Adds the broader discipline for deciding difficult trade-offs fairly.",
    },
    {
        "benchmark_id": "general-guide-competing-stakeholder-obligations-gold-standard-2026-10-26",
        "role": "conditional",
        "condition": "The question explicitly concerns multiple affected parties or competing obligations.",
        "rationale": "Adds stakeholder rights, obligations, burdens, and review where those are explicit.",
    },
    {
        "benchmark_id": "gs-2026-11-20-power-responsibility-proportional-accountability",
        "role": "conditional",
        "condition": "The question explicitly raises power, authority, influence, or unequal responsibility.",
        "rationale": "Connects decision influence and capacity to proportionate answerability.",
    },
    {
        "benchmark_id": "gs-2026-11-20-stewardship-consent-relational-legitimacy",
        "role": "conditional",
        "condition": "The question explicitly raises freedom, autonomy, consent, or participation.",
        "rationale": "Protects affected people's agency and distinguishes responsibility from authority.",
    },
)


def _matches(query: str) -> bool:
    q = re.sub(r"\s+", " ", str(query or "").casefold()).strip()
    community = bool(re.search(r"\b(?:community|communit(?:y|ies)|group|collective|members|shared)\b", q))
    freedom = bool(re.search(r"\b(?:freedom|libert\w*|autonom\w*|individual rights?|consent|participation)\b", q))
    responsibility = bool(re.search(r"\b(?:responsib\w*|accountab\w*|obligations?|duty|duties)\b", q))
    decision = bool(re.search(r"\b(?:decid\w*|decision\w*|trade[- ]?off|conflict\w*|fair\w*|workable)\b", q))
    return community and freedom and responsibility and decision


def select_community_tradeoff_candidates(
    query: str,
    lessons: List[Dict[str, Any]],
) -> Optional[List[Dict[str, Any]]]:
    """Return a bounded governed set, None outside this precise question family."""
    q = re.sub(r"\s+", " ", str(query or "").casefold()).strip()
    if not _matches(q):
        return None

    modes = {"core"}
    if re.search(r"\b(?:rule|rules|policy|policies|restriction\w*|limit\w*)\b", q):
        modes.add("conditional:rule_design")
    if re.search(r"\b(?:trade[- ]?off|conflict\w*|competing obligations|competing values|competing interests)\b", q):
        modes.add("conditional:ethical_tradeoff")
    if re.search(r"\b(?:stakeholder\w*|affected parties|competing obligations|multiple parties)\b", q):
        modes.add("conditional:stakeholders")
    if re.search(r"\b(?:power|authority|influence|unequal|least power|burden\w*)\b", q):
        modes.add("conditional:power")
    if re.search(r"\b(?:freedom|libert\w*|autonom\w*|individual rights?|consent|participation)\b", q):
        modes.add("conditional:consent")

    by_id = {
        str(item.get("id") or ""): item
        for item in lessons
        if isinstance(item, dict) and item.get("runtime_transfer") is True
    }
    selected = []
    for definition in _CANDIDATES:
        key = {
            "core": "core",
            "conditional": (
                "conditional:stakeholders"
                if "ethical-tradeoff" in definition["benchmark_id"]
                else "conditional:stakeholders"
                if "stakeholder" in definition["benchmark_id"]
                else "conditional:power"
                if "power-responsibility" in definition["benchmark_id"]
                else "conditional:rule_design"
                if "community-rule-design" in definition["benchmark_id"]
                else "conditional:consent"
            ),
        }[definition["role"]]
        if key not in modes:
            continue
        lesson = by_id.get(definition["benchmark_id"])
        if lesson is None:
            return []
        selected.append({
            "lesson": lesson,
            "role": definition["role"],
            "activation_condition": definition["condition"],
            "role_rationale": definition["rationale"],
        })
    return selected if len(selected) <= MAX_POLICY_CANDIDATES else []
