"""Deterministic-first routing registry for the Living Archive Guide.

Routing is a governed rules decision, not an LLM task. Unknown queries remain
in the Guide's general inquiry lane; specialist routes require explicit,
testable signals. Safety and explicit user task intent have defined precedence.
This module does not generate answers, retrieve assets, or invoke specialists.
"""
from __future__ import annotations

from dataclasses import dataclass
import re


ROUTING_REGISTRY_VERSION = "v1"


@dataclass(frozen=True)
class RouteDecision:
    route: str
    mode: str
    confidence: float
    reason: str
    source: str
    alternatives: tuple[str, ...] = ("guide",)


@dataclass(frozen=True)
class RouteRule:
    route: str
    mode: str
    priority: int
    reason: str
    source: str
    patterns: tuple[str, ...]
    confidence: float = 0.95
    exclusions: tuple[str, ...] = ()


# High-precision task signals only. Broad topic matching is intentionally avoided.
_RULES = (
    RouteRule(
        route="catalogue", mode="lookup", priority=80,
        reason="explicit Catalogue/resource discovery request",
        source="deterministic-catalogue-task",
        patterns=(
            r"\b(?:find|search for|look for|discover)\b.{0,100}\b(?:catalogue|catalog|case studies|cases|archive resources|stewardship resources)\b",
            r"\b(?:catalogue|catalog)\b.{0,80}\b(?:search|find|discover|browse)\b",
        ),
        confidence=0.97,
    ),
    RouteRule(
        route="formation", mode="delegated_journey", priority=70,
        reason="explicit Formation entry or preparation request",
        source="deterministic-formation-entry",
        patterns=(
            r"\b(?:stewardship formation|formation navigator|formation pathway)\b",
            r"\b(?:prepare|preparing|training|readiness|learning|learn|develop)\b.{0,100}\b(?:stewardship|steward|governance|shared responsibility)\b.{0,100}\b(?:enter|start|begin|join|access|open|launch|pathway)\b",
        ),
        confidence=0.96,
        exclusions=(r"\b(?:what is|explain|define|meaning of)\b",),
    ),
    RouteRule(
        route="fsd", mode="direct", priority=95,
        reason="explicit Fractal Systems Diagnostic request",
        source="deterministic-fsd-task",
        patterns=(
            r"\b(?:fractal systems diagnostic|fsd diagnostic|run an fsd|use fsd)\b",
        ),
        confidence=0.98,
    ),
    RouteRule(
        route="glyph", mode="lookup", priority=75,
        reason="explicit glyph or symbol lookup request",
        source="deterministic-glyph-lookup",
        patterns=(
            r"\b(?:glyph|symbol|icon|mark)\b.{0,80}\b(?:find|show|lookup|look up|meaning|what does)\b",
            r"\b(?:find|show|lookup|look up)\b.{0,80}\b(?:glyph|symbol|icon|mark)\b",
        ),
    ),
    RouteRule(
        route="atlas", mode="lookup", priority=75,
        reason="explicit Atlas/reference-map discovery request",
        source="deterministic-atlas-lookup",
        patterns=(
            r"\b(?:atlas|reference map|maps of the archive)\b.{0,80}\b(?:find|show|explore|lookup|look up|browse)\b",
            r"\b(?:find|show|explore|lookup|look up|browse)\b.{0,90}\b(?:visual )?maps?\b",
        ),
        exclusions=(r"\b(?:google maps|directions to|route to)\b",),
    ),
    RouteRule(
        route="glossary", mode="lookup", priority=50,
        reason="explicit bounded definition or meaning request",
        source="deterministic-glossary-lookup",
        patterns=(
            r"\b(?:define|definition of|what is|what does .{1,70} mean|meaning of)\b",
        ),
        exclusions=(
            r"\b(?:stewardship)\b.{0,100}\b(?:practice|practise|everyday|daily|decisions?|responsibilities|community|communities)\b",
            r"\b(?:practice|practise|everyday|daily|decisions?|responsibilities|community|communities)\b.{0,100}\bstewardship\b",
        ),
    ),
    RouteRule(
        route="relationship", mode="specialist", priority=60,
        reason="explicit relational situation or relationship interpretation request",
        source="deterministic-relational-intent",
        patterns=(
            r"\b(?:help me understand|make sense of|navigate|work through)\b.{0,100}\b(?:relationship|conflict between|tension with|misunderstanding with|trust between)\b",
            r"\b(?:what is happening between us|why do we keep arguing|different perspectives in this relationship)\b",
        ),
        confidence=0.91,
    ),
)


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").casefold()).strip()


def _matches(patterns: tuple[str, ...], query: str) -> bool:
    return any(re.search(pattern, query, re.I) for pattern in patterns)


def resolve_route(query: str, *, safety_active: bool = False) -> RouteDecision:
    """Resolve a high-precision route without any model call.

    The existing authoritative safety boundary must run before ordinary routing.
    Unknown or mixed queries default to the Guide rather than triggering a
    second model call solely for classification.
    """
    q = _normalize(query)
    if safety_active:
        return RouteDecision(
            route="safety", mode="safety", confidence=1.0,
            reason="authoritative safety boundary is active",
            source="deterministic-safety-precedence", alternatives=("guide",),
        )
    if not q:
        return RouteDecision(
            route="guide", mode="clarify", confidence=1.0,
            reason="empty query requires clarification",
            source="deterministic-empty-query", alternatives=(),
        )

    candidates = [
        rule for rule in _RULES
        if _matches(rule.patterns, q) and not _matches(rule.exclusions, q)
    ]
    if candidates:
        chosen = sorted(candidates, key=lambda item: (-item.priority, item.route))[0]
        return RouteDecision(
            route=chosen.route, mode=chosen.mode, confidence=chosen.confidence,
            reason=chosen.reason, source=chosen.source,
            alternatives=("guide",),
        )

    return RouteDecision(
        route="guide", mode="direct", confidence=0.80,
        reason="no high-precision specialist rule matched; retain general inquiry in Guide",
        source="deterministic-guide-default", alternatives=(),
    )


def registry_snapshot() -> dict:
    return {
        "version": ROUTING_REGISTRY_VERSION,
        "rules": len(_RULES),
        "routes": sorted({rule.route for rule in _RULES} | {"guide", "safety"}),
        "fallback": "guide",
        "uses_llm_for_routing": False,
    }
