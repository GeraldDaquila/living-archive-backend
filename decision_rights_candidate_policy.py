"""Governed decision-rights candidate-set activation.

This policy consumes the canonical initialization benchmark as role/condition
metadata. It does not transfer exemplar answers, claims, citations, or doorways.
A recognized institutional decision-rights query receives the core discipline
set; conditional disciplines are added only when their explicit trigger exists.
Unrelated and underspecified questions return None so the ordinary selector
continues unchanged.
"""
from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

_LOG = logging.getLogger("use.gold_star.decision_rights_policy")
_POLICY_PATH = Path(__file__).resolve().parent / "docs" / "qa" / "decision_rights_candidate_set_benchmark.json"

@lru_cache(maxsize=1)
def _benchmark() -> Optional[Dict[str, Any]]:
    try:
        value = json.loads(_POLICY_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        _LOG.exception("decision-rights policy benchmark unavailable")
        return None
    roles = value.get("candidate_roles") if isinstance(value, dict) else None
    if not isinstance(roles, list) or not roles:
        _LOG.error("decision-rights policy benchmark has no candidate roles")
        return None
    ids = [str(item.get("benchmark_id") or "").strip() for item in roles if isinstance(item, dict)]
    if len(ids) != len(roles) or not all(ids) or len(ids) != len(set(ids)):
        _LOG.error("decision-rights policy benchmark candidate identity is invalid")
        return None
    return value


def _query_mode(query: str) -> Optional[set[str]]:
    q = re.sub(r"\s+", " ", str(query or "").casefold()).strip()
    if not q:
        return None

    # This neighboring discipline is intentionally isolated: it is not a
    # default part of the institutional decision-rights core set.
    leadership_contrast = (
        bool(re.search(r"\bleadership\b", q))
        and (
            bool(re.search(r"\bpositional authority\b", q))
            or bool(re.search(r"\btitle\b.{0,90}\b(?:lead|leadership)\b|\b(?:lead|leadership)\b.{0,90}\btitle\b", q))
        )
    )
    if leadership_contrast:
        return {"related_conditional"}

    institutional = bool(re.search(
        r"\b(?:institution\w*|organization\w*|organisation\w*|governance|board|committee|nonprofit|agency)\b",
        q,
    ))
    accountability = bool(re.search(
        r"\b(?:responsib\w*|accountab\w*|answerab\w*|answer for|who should answer|who remains accountable)\b",
        q,
    ))
    power_or_rights = bool(re.search(
        r"\b(?:decision rights?|decision-making authority|formal authority|actual power|actual say|influence|who gets heard|who decides)\b",
        q,
    ))
    decision_context = bool(re.search(r"\bdecision\w*\b", q))
    delegated = bool(re.search(r"\bdelegat(?:e|es|ed|ing|ion)\b", q))
    board_committee = bool(re.search(r"\bboard\b", q) and bool(re.search(r"\bcommittee\b", q)))

    formal_informal = (
        institutional
        and bool(re.search(r"\b(?:formal|written|bylaw|rules?)\b", q))
        and bool(re.search(r"\binformal\b", q))
        and bool(re.search(r"\b(?:norms?|practice|workarounds?|heard|decided|influence)\b", q))
    )
    delegation_context = (
        delegated
        and (institutional or board_committee)
        and (accountability or decision_context)
    )

    core_context = (
        (power_or_rights and accountability and (institutional or decision_context))
        or (institutional and decision_context and accountability and bool(re.search(r"\b(?:authority|influence|power|rights?)\b", q)))
        or delegation_context
        or formal_informal
    )
    if not core_context:
        return None

    roles = {"core"}
    if delegation_context:
        roles.add("conditional:delegation")
    if formal_informal:
        roles.add("conditional:formal_informal")
    return roles


def select_policy_candidates(
    query: str,
    lessons: List[Dict[str, Any]],
) -> Optional[List[Dict[str, Any]]]:
    """Return policy-selected lesson/role pairs, None when this policy does not apply.

    An empty list means the query clearly matched this governed family but its
    canonical candidate inventory was not available or eligible; callers must
    fail closed rather than fall through to broad semantic analogies.
    """
    modes = _query_mode(query)
    if modes is None:
        return None
    benchmark = _benchmark()
    if benchmark is None:
        return []
    by_id = {
        str(item.get("id") or ""): item
        for item in lessons
        if isinstance(item, dict) and item.get("runtime_transfer") is True
    }
    selected: List[Dict[str, Any]] = []
    for definition in benchmark["candidate_roles"]:
        role = str(definition.get("role") or "")
        condition_key = None
        if role == "core":
            condition_key = "core"
        elif role == "conditional" and definition.get("benchmark_id") == "general-guide-delegated-judgment-moral-limits-gold-star-2026-11-13":
            condition_key = "conditional:delegation"
        elif role == "conditional" and definition.get("benchmark_id") == "general-guide-formal-informal-institutional-dynamics-gold-star-2026-11-18":
            condition_key = "conditional:formal_informal"
        elif role == "related_conditional":
            condition_key = "related_conditional"
        if condition_key not in modes:
            continue
        benchmark_id = str(definition.get("benchmark_id") or "")
        lesson = by_id.get(benchmark_id)
        if lesson is None:
            _LOG.error("decision-rights policy candidate unavailable id=%s", benchmark_id)
            return []
        selected.append({
            "lesson": lesson,
            "role": role,
            "activation_condition": str(definition.get("condition") or ""),
            "role_rationale": str(definition.get("rationale") or ""),
        })
    return selected
