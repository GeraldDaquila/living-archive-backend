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
            r"\b(?:find|search for|look for|discover)\b.{0,100}\b(?:catalogue|catalog|archive resources|stewardship resources)\b",
            r"\b(?:catalogue|catalog)\b.{0,80}\b(?:search|find|discover|browse)\b",
        ),
        confidence=0.97,
    ),
    RouteRule(
        route="formation", mode="delegated_journey", priority=70,
        reason="explicit Formation entry or preparation request",
        source="deterministic-formation-entry",
        patterns=(
            r"\b(?:open|launch|enter|start|begin|join|access|use|take me to)\b.{0,80}\b(?:stewardship formation|formation navigator|formation pathway)\b",
            r"\b(?:stewardship formation|formation navigator|formation pathway)\b.{0,60}\b(?:open|launch|enter|start|begin|join|access|use)\b",
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
            r"\bwhat does\b.{0,60}\b(?:glyph|symbol|icon|mark)\b.{0,30}\bmean\b",
        ),
    ),
    RouteRule(
        route="atlas", mode="lookup", priority=75,
        reason="explicit Atlas/reference-map discovery request",
        source="deterministic-atlas-lookup",
        patterns=(
            r"\b(?:atlas|archive reference map|reference map of the archive|maps of the archive|archive map)\b.{0,80}\b(?:find|show|explore|lookup|look up|browse|open)\b",
            r"\b(?:find|show|explore|lookup|look up|browse|open)\b.{0,90}\b(?:archive atlas|archive reference map|reference map of the archive|maps of the archive|archive map)\b",
        ),
        exclusions=(r"\b(?:google maps|directions to|route to)\b",),
    ),
    RouteRule(
        route="glossary", mode="lookup", priority=50,
        reason="explicit bounded definition or meaning request",
        source="deterministic-glossary-lookup",
        patterns=(
            r"\b(?:define|definition of|what does .{1,70} mean|meaning of)\b",
        ),
        exclusions=(
            r"\b(?:stewardship)\b.{0,100}\b(?:practice|practise|everyday|daily|decisions?|responsibilities|community|communities)\b",
            r"\b(?:practice|practise|everyday|daily|decisions?|responsibilities|community|communities)\b.{0,100}\bstewardship\b",
            r"\bstewardship\b.{0,80}\b(?:and why|why does|why it matters|and how|in practice)\b",
            r"\b(?:and why|why does|why it matters|and how|in practice)\b.{0,80}\bstewardship\b",
            r"\bmeaning of (?:a )?(?:good )?life\b",
        ),
    ),
    RouteRule(
        route="navigator", mode="lookup", priority=65,
        reason="explicit whole-Archive orientation or entry request",
        source="deterministic-archive-orientation",
        patterns=(
            r"\b(?:where do i|where should i|how do i|how can i)\b.{0,80}\b(?:begin|start|enter|navigate)\b.{0,100}\b(?:living archive|archive)\b",
            r"\b(?:help me find my way|orient me|show me where to begin)\b.{0,80}\b(?:living archive|archive)\b",
            r"\b(?:living archive|archive)\b.{0,80}\b(?:where to begin|how to navigate|how to enter|orientation)\b",
        ),
        confidence=0.92,
    ),
    RouteRule(
        route="systems_ph", mode="lookup", priority=85,
        reason="explicit Philippine Systems Lens request",
        source="deterministic-philippine-systems-lens",
        patterns=(
            r"\b(?:open|launch|enter|use|run|apply|invoke)\b.{0,80}\b(?:philippine systems lens|systems lens for the philippines|philippines systems lens)\b",
            r"\b(?:philippine systems lens|systems lens for the philippines|philippines systems lens)\b.{0,80}\b(?:open|launch|enter|use|run|apply|invoke)\b",
        ),
        exclusions=(r"\b(?:do not|don\x27t|never)\b.{0,40}\b(?:open|launch|enter|use|run|apply|invoke)\b",),
        confidence=0.98,
    ),
    RouteRule(
        route="case", mode="lookup", priority=75,
        reason="explicit case-study discovery request",
        source="deterministic-case-study-lookup",
        patterns=(
            r"\b(?:find|show|search for|look for)\b.{0,80}\b(?:case studies|case study|relevant cases|matching cases)\b",
            r"\b(?:case studies|case study|relevant cases|matching cases)\b.{0,80}\b(?:find|show|search|browse)\b",
        ),
    ),
    RouteRule(
        route="relationship", mode="delegated_journey", priority=60,
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


def _is_lived_relational_projection_query(query: str) -> bool:
    """Recognize a narrow first-person relational-uncertainty pattern, not topic mentions."""
    if not query:
        return False
    bounded_resource_request = re.search(
        r"\b(?:find|search|browse|recommend|show me|locate)\b.{0,100}"
        r"\b(?:article|articles|resources?|materials?|works?|readings?)\b",
        query,
    )
    archive_resource_request = re.search(r"\b(?:living archive|archive|catalogue|catalog)\b", query)
    if bounded_resource_request and archive_resource_request:
        return False

    first_person = re.search(r"\b(?:i|i'm|i am|i can't|i cannot|i don't|i do not|my)\b", query)
    relational_term = re.search(
        r"\b(?:relationship|between us|partner|colleague|friendship|family|we)\b", query
    )
    dynamic_term = re.search(
        r"\b(?:sensing|projecting|projection|what i'm feeling|what i'm sensing|"
        r"what is happening|what's happening|misreading|reacting)\b",
        query,
    )
    inquiry_term = re.search(
        r"\b(?:can't tell|cannot tell|not sure|wonder|trying to understand|"
        r"trying to make sense|whether|is real|am i|could be)\b",
        query,
    )
    return bool(first_person and relational_term and dynamic_term and inquiry_term)


def _is_catalogue_resource_search(query: str) -> bool:
    """Mirror the bounded production Catalogue task boundary without importing main."""
    if not query:
        return False

    resource_noun = (
        r"(?:resources?|materials?|sources?|works?|essays?|articles?|cases?|"
        r"readings?|publications?|texts?|information|content)"
    )
    if re.search(rf"^(?:what|which)\s+{resource_noun}\b", query):
        return True

    search_pattern = re.compile(
        rf"\b(?:where can i find|where do i find|how can i find|"
        rf"find(?: me)?|search(?: for| the archive| the catalogue| the catalog)|"
        rf"browse|explore|look(?:ing)? for|locate|recommend|suggest|"
        rf"show me|list|give me|provide|surface|open)\b"
        rf".{{0,120}}\b{resource_noun}\b"
    )
    catalogue_pattern = re.compile(
        r"\b(?:browse|explore|search|open)\s+(?:the\s+)?"
        r"(?:catalogue|catalog|archive)\b"
    )
    match = search_pattern.search(query)
    if not match and not catalogue_pattern.search(query):
        return False

    explanatory_pattern = re.compile(
        r"\b(?:what is|what are|why is|why are|why does|why do|"
        r"explain|how does|how do|how is|how are)\b"
    )
    explanatory = explanatory_pattern.search(query)
    if explanatory and match and explanatory.start() < match.start():
        return False
    if explanatory and not match:
        return False
    return True

_NEGATED_TASK_PATTERN = re.compile(
    r"\b(?:do not|don't|never|please do not|please don't)\s+"
    r"(?:please\s+)?(?:find|search|look for|discover|open|launch|enter|start|begin|"
    r"join|access|use|take me to|run|apply|invoke|show|explore|lookup|look up|browse|define)\b",
    re.I,
)


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
    # A contrastive clause can reject one action while affirming another.
    # Keep the conservative whole-query guard for coordinated negation ("... or ..."),
    # but evaluate the affirmative clause after an explicit "but" independently.
    contrastive = re.split(r"\s+but\s+", q, maxsplit=1)
    if len(contrastive) == 2 and _NEGATED_TASK_PATTERN.search(contrastive[0]):
        q = contrastive[1].strip()
    elif _NEGATED_TASK_PATTERN.search(q):
        return RouteDecision(
            route="guide", mode="direct", confidence=0.90,
            reason="negated task intent is not delegated to a specialist",
            source="deterministic-negated-task-guard", alternatives=(),
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

    # Preserve the production relational boundary's multi-signal character:
    # first-person + relational context + dynamic interpretation + inquiry.
    if _is_lived_relational_projection_query(q):
        return RouteDecision(
            route="relationship", mode="delegated_journey", confidence=0.93,
            reason="first-person relational uncertainty with projection/dynamic signals",
            source="deterministic-lived-relational-projection", alternatives=("guide",),
        )

    # Specific bounded specialist rules take precedence over this broader
    # resource-discovery predicate; unknown/explanatory queries remain Guide.
    if _is_catalogue_resource_search(q):
        return RouteDecision(
            route="catalogue", mode="lookup", confidence=0.96,
            reason="explicit natural-language resource discovery request",
            source="deterministic-catalogue-resource-search", alternatives=("guide",),
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
