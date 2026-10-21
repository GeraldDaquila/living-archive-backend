"""Explainable, dependency-free fuzzy relevance scoring for The Guide.

This first version is SHADOW ONLY: scores are diagnostic signals and must not
change candidate eligibility, ranking, response text, or resource selection.
The feature groups are intentionally general and interpretable; they are not a
claim of embedding-based semantic understanding.
"""
import re

CONCEPTS = {
    "ethical_tradeoff": (
        "tradeoff", "trade-offs", "trade off", "conflicting harms", "competing harms",
        "ethical conflict", "conflict", "different harm", "another group", "repairing harm",
        "competing values", "sacrifice", "burden", "consequences",
        "fair process", "alternatives", "decision criteria", "who bears",
    ),
    "harm_repair": (
        "repair", "reparation", "restorative justice", "restitution", "redress",
        "make amends", "repairing harm", "affected people", "people harmed",
        "losses", "what was lost", "survivors", "voice", "participation",
    ),
    "accountability": (
        "accountability", "responsibility", "evidence", "warnings", "dissent",
        "review the outcome", "learn from", "foreseeable risks",
    ),
    "governance": (
        "governance", "decision-making", "stewardship", "institutions",
        "policy", "collective decision", "public decision",
    ),
    "belonging_identity": (
        "belonging", "group affiliation", "authenticity", "identity",
        "community membership", "group identity",
    ),
    "power_fairness": (
        "power", "unequal power", "least power", "rights", "fairness",
        "disproportionate", "voice", "consent", "affected people",
    ),
}


def _normalize(value):
    value = str(value or "").casefold().replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s'-]", " ", value)).strip()


def _membership(text, phrases):
    """Return graded phrase coverage, not a binary semantic judgment."""
    normalized = _normalize(text)
    if not normalized:
        return 0.0
    hits = sum(1 for phrase in phrases if _normalize(phrase) in normalized)
    return min(1.0, hits / max(3.0, min(6.0, len(phrases) * 0.5)))


def score_resource_fit(query, document):
    """Return transparent 0..1 dimension scores for shadow evaluation only."""
    if not isinstance(document, dict):
        document = {}
    title = str(document.get("title") or "")
    body = str(document.get("text") or document.get("content") or document.get("excerpt") or "")
    q = _normalize(query)
    full_text = _normalize(title + " " + body)
    query_tokens = {t for t in re.findall(r"[a-z0-9]+", q) if len(t) > 3}
    title_tokens = {t for t in re.findall(r"[a-z0-9]+", _normalize(title)) if len(t) > 3}
    body_tokens = {t for t in re.findall(r"[a-z0-9]+", _normalize(body)) if len(t) > 3}
    title_overlap = len(query_tokens & title_tokens) / max(1, len(query_tokens))
    body_overlap = len(query_tokens & body_tokens) / max(1, len(query_tokens))
    dimensions = {
        # A concept contributes only when it is present in both the question
        # and the candidate. This prevents a resource from scoring positively
        # merely because it contains a concept unrelated to the visitor's ask.
        name: round(
            _membership(q, phrases)
            * (0.35 * _membership(title, phrases) + 0.65 * _membership(body, phrases)),
            4,
        )
        for name, phrases in CONCEPTS.items()
    }
    dimensions["query_title_overlap"] = round(title_overlap, 4)
    dimensions["query_body_overlap"] = round(body_overlap, 4)
    # General score supports comparison only. Hard safety/evidence gates remain
    # outside this function and must never be averaged away.
    concept_scores = [v for k, v in dimensions.items() if k not in {"query_title_overlap", "query_body_overlap"}]
    dimensions["overall_shadow_score"] = round(
        0.35 * max(concept_scores, default=0.0)
        + 0.25 * (sum(concept_scores) / max(1, len(concept_scores)))
        + 0.20 * title_overlap
        + 0.20 * body_overlap,
        4,
    )
    return dimensions
