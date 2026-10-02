"""Draft shared reasoning primitives for USE and bounded operating modes.

This module is deliberately pure and authority-free. It does not retrieve,
route, select canonical resources authoritatively, call a model, or generate
final visitor-facing prose.

It is a candidate extraction from the implementation archaeology only.
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
    """Normalize candidate doorways; never establishes canonical authority."""
    output: list[DoorwayCandidate] = []
    seen: set[str] = set()

    for item in candidates:
        if not isinstance(item, Mapping):
            continue

        title = _clean(item.get("title"))
        url = str(item.get("url") or item.get("canonical_url") or "").strip()

        if not title or not _valid_https_url(url) or url in seen:
            continue

        seen.add(url)

        rank = item.get("candidate_rank")
        try:
            rank = int(rank) if rank is not None else None
        except (TypeError, ValueError):
            rank = None

        output.append(
            DoorwayCandidate(
                title=title,
                url=url,
                relevance_basis=_clean(item.get("relevance_basis")),
                source_ids=tuple(str(x) for x in item.get("source_ids", ())),
                candidate_rank=rank,
            )
        )

    return tuple(output)


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
