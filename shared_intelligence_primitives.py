"""Shared reasoning primitives for bounded USE production seams.

This module is deliberately pure and authority-free. It does not retrieve,
route, select canonical resources authoritatively, call a model, or generate
final visitor-facing prose.

Active production seams currently cover evidence normalization, claim
normalization, synthesis-material packaging, bounded doorway normalization,
and bounded journey-contribution normalization. Other primitives remain inert
until separately introduced and validated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlparse
import re


CONTRACT_VERSION = "v1"

READY = "READY"
DELEGATE = "DELEGATE"
NEEDS_RETRY = "NEEDS_RETRY"
UNAVAILABLE = "UNAVAILABLE"

ALLOWED_STATUSES = frozenset({READY, DELEGATE, NEEDS_RETRY, UNAVAILABLE})
ALLOWED_CLAIM_TYPES = frozenset(
    {"definition", "relationship", "observation", "interpretation", "exploration"}
)
ALLOWED_EPISTEMIC = frozenset(
    {"supported", "inferred", "interpretive", "visitor-originated", "uncertain"}
)


@dataclass(frozen=True)
class EvidenceItem:
    id: str
    title: str
    url: str
    text: str
    provenance: str = "supplied"


@dataclass(frozen=True)
class Claim:
    text: str
    evidence_ids: tuple[str, ...] = ()
    claim_type: str = "exploration"
    epistemic: str = "uncertain"
    confidence: float | None = None


@dataclass(frozen=True)
class InquiryMovement:
    surface_input: str
    dimensions: Mapping[str, Any] = field(default_factory=dict)
    human_situation: Any = None
    desired_movement: Any = None
    uncertainty: Any = None
    processing_need: Any = None
    stage: Any = None


@dataclass(frozen=True)
class SynthesisMaterial:
    claims: tuple[Claim, ...] = ()
    relationship_statement: str = ""
    unresolved_tensions: tuple[str, ...] = ()
    perspective_options: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class DoorwayCandidate:
    title: str
    url: str
    relevance_basis: str = ""
    source_ids: tuple[str, ...] = ()
    candidate_rank: int | None = None


@dataclass(frozen=True)
class JourneyContribution:
    """Bounded closure material received by USE from a completed specialist journey."""

    original_question: str = ""
    conversation: str = ""
    thread_summary: str = ""
    working_hypothesis: str = ""
    completed_insight: str = ""
    perspective_delta: str = ""
    body_of_thought: str = ""
    underlying_need: str = ""
    desired_condition: str = ""
    next_horizon: str = ""
    resource_fit: str = ""
    journey_synthesis: str = ""
    journey_action: str = ""
    journey_ledger: Mapping[str, Any] = field(default_factory=dict)
    fractal_records: tuple[Any, ...] = ()
    round_synthesis_history: tuple[Any, ...] = ()


@dataclass(frozen=True)
class OperationResult:
    status: str
    mode: str
    payload: Any = None
    reason: str = ""
    contract_version: str = CONTRACT_VERSION


def _clean(value: Any) -> str:
    value = re.sub(r"<[^>]+>", " ", str(value or ""))
    value = re.sub(r"https?://\S+|www\.\S+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _valid_https_url(value: Any) -> bool:
    raw = str(value or "").strip()
    try:
        parsed = urlparse(raw)
    except ValueError:
        return False
    return parsed.scheme.lower() == "https" and bool(parsed.netloc)


def normalize_evidence(
    documents: Iterable[Mapping[str, Any]],
    *,
    provenance: str = "supplied",
) -> tuple[EvidenceItem, ...]:
    """Clean, validate, and deduplicate source material."""
    output: list[EvidenceItem] = []
    seen: set[tuple[str, str]] = set()
    clean_provenance = _clean(provenance) or "supplied"

    for document in documents:
        if not isinstance(document, Mapping):
            continue

        title = _clean(document.get("title"))
        url = str(document.get("url") or document.get("canonical_url") or "").strip()
        text = _clean(
            document.get("text")
            or document.get("content")
            or document.get("excerpt")
        )

        if not title or not _valid_https_url(url) or not text:
            continue

        key = (url, title.casefold())
        if key in seen:
            continue
        seen.add(key)

        item_id = _clean(document.get("id"))
        if not item_id:
            item_id = f"source:{len(output) + 1}"

        output.append(
            EvidenceItem(
                id=item_id,
                title=title,
                url=url,
                text=text,
                provenance=clean_provenance,
            )
        )

    return tuple(output)


def _claim_key(text: str) -> str:
    return re.sub(r"\W+", " ", text.casefold()).strip()


def normalize_claims(
    claims: Iterable[Mapping[str, Any]],
    *,
    evidence_ids: Iterable[str] = (),
) -> tuple[Claim, ...]:
    """Normalize claims without merging independent propositions."""
    allowed_evidence = {str(x) for x in evidence_ids}
    output: list[Claim] = []
    seen: set[str] = set()

    for item in claims:
        if not isinstance(item, Mapping):
            continue

        text = _clean(item.get("text"))
        if not text:
            continue

        key = _claim_key(text)
        if not key or key in seen:
            continue
        seen.add(key)

        refs = tuple(
            str(ref)
            for ref in item.get("evidence_ids", ())
            if str(ref) in allowed_evidence
        )

        claim_type = str(item.get("claim_type") or "exploration")
        if claim_type not in ALLOWED_CLAIM_TYPES:
            claim_type = "exploration"

        epistemic = str(item.get("epistemic") or "uncertain")
        if epistemic not in ALLOWED_EPISTEMIC:
            epistemic = "uncertain"

        confidence = item.get("confidence")
        if confidence is not None:
            try:
                confidence = max(0.0, min(1.0, float(confidence)))
            except (TypeError, ValueError):
                confidence = None

        output.append(
            Claim(
                text=text,
                evidence_ids=refs,
                claim_type=claim_type,
                epistemic=epistemic,
                confidence=confidence,
            )
        )

    return tuple(output)


def build_epistemic_tag(
    *,
    supported: bool = False,
    inferred: bool = False,
    interpretive: bool = False,
    visitor_originated: bool = False,
    uncertain: bool = False,
) -> str:
    """Return one explicit epistemic treatment tag.

    Visitor-originated and uncertain material take precedence so it cannot be
    silently promoted into source-supported fact.
    """
    if visitor_originated:
        return "visitor-originated"
    if uncertain:
        return "uncertain"
    if interpretive:
        return "interpretive"
    if inferred:
        return "inferred"
    if supported:
        return "supported"
    return "uncertain"


def build_synthesis_material(
    claims: Sequence[Claim],
    *,
    relationship_statement: str = "",
    unresolved_tensions: Sequence[str] = (),
    perspective_options: Sequence[str] = (),
) -> SynthesisMaterial:
    """Package synthesis material without asserting unsupported relationships."""
    clean_claims = tuple(claim for claim in claims if isinstance(claim, Claim))
    source_ids = tuple(
        dict.fromkeys(
            ref
            for claim in clean_claims
            for ref in claim.evidence_ids
        )
    )
    clean_tensions = tuple(
        value for value in (_clean(x) for x in unresolved_tensions) if value
    )
    clean_perspectives = tuple(
        value for value in (_clean(x) for x in perspective_options) if value
    )

    return SynthesisMaterial(
        claims=clean_claims,
        relationship_statement=_clean(relationship_statement),
        unresolved_tensions=clean_tensions,
        perspective_options=clean_perspectives,
        source_ids=source_ids,
    )


def normalize_doorway_candidates(
    candidates: Iterable[Mapping[str, Any]],
) -> tuple[DoorwayCandidate, ...]:
    """Normalize supplied doorway candidates without choosing among them."""
    output: list[DoorwayCandidate] = []
    seen_urls: set[str] = set()
    next_rank = 1

    for item in candidates:
        if not isinstance(item, Mapping):
            continue

        title = _clean(item.get("title"))
        url = str(item.get("url") or item.get("canonical_url") or "").strip()

        if not title or not _valid_https_url(url):
            continue

        url_key = url.rstrip("/").casefold()
        if url_key in seen_urls:
            continue
        seen_urls.add(url_key)

        relevance_basis = _clean(item.get("relevance_basis"))
        source_ids = tuple(
            ref for ref in (_clean(x) for x in item.get("source_ids", ())) if ref
        )

        raw_rank = item.get("candidate_rank")
        try:
            rank = int(raw_rank) if raw_rank is not None else None
        except (TypeError, ValueError):
            rank = None

        if rank is None or rank < 1:
            rank = next_rank
        next_rank = max(next_rank + 1, rank + 1)

        output.append(
            DoorwayCandidate(
                title=title,
                url=url,
                relevance_basis=relevance_basis,
                source_ids=source_ids,
                candidate_rank=rank,
            )
        )

    return tuple(output)

def normalize_journey_contribution(
    contribution: Mapping[str, Any],
) -> JourneyContribution:
    """Normalize completed journey material without assigning authority."""
    if not isinstance(contribution, Mapping):
        raise ValueError("Journey contribution must be a mapping.")

    def _text(name: str) -> str:
        return _clean(contribution.get(name))

    ledger = contribution.get("journey_ledger")
    if not isinstance(ledger, Mapping):
        ledger = {}

    def _sequence(name: str) -> tuple[Any, ...]:
        value = contribution.get(name)
        if isinstance(value, (list, tuple)):
            return tuple(value)
        return ()

    return JourneyContribution(
        original_question=_text("original_question"),
        conversation=_text("conversation"),
        thread_summary=_text("thread_summary"),
        working_hypothesis=_text("working_hypothesis"),
        completed_insight=_text("completed_insight"),
        perspective_delta=_text("perspective_delta"),
        body_of_thought=_text("body_of_thought"),
        underlying_need=_text("underlying_need"),
        desired_condition=_text("desired_condition"),
        next_horizon=_text("next_horizon"),
        resource_fit=_text("resource_fit"),
        journey_synthesis=_text("journey_synthesis"),
        journey_action=_text("journey_action").casefold(),
        journey_ledger=dict(ledger),
        fractal_records=_sequence("fractal_records"),
        round_synthesis_history=_sequence("round_synthesis_history"),
    )


def operation_result(
    status: str,
    *,
    mode: str,
    payload: Any = None,
    reason: str = "",
) -> OperationResult:
    status = str(status or "").strip().upper()
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"Unsupported operation status: {status}")

    if status == READY and payload is None:
        raise ValueError("READY requires payload")

    if status != READY and not _clean(reason):
        raise ValueError(f"{status} requires an explicit reason")

    return OperationResult(
        status=status,
        mode=str(mode or "").strip(),
        payload=payload,
        reason=_clean(reason),
    )


def visitor_language_ready(text: Any) -> bool:
    """Minimal boundary check; active modes retain their own visitor policies."""
    value = str(text or "").strip()
    if not value:
        return False

    forbidden = (
        "EvidenceItem(",
        "OperationResult(",
        "InquiryMovement(",
        "DoorwayCandidate(",
        "contract_version=",
        "internal specialist",
    )
    return not any(marker.casefold() in value.casefold() for marker in forbidden)
