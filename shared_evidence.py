"""Production seam for the shared evidence normalization primitive.

The seam is intentionally narrow: it normalizes already-retrieved document
mappings into the legacy dictionary shape consumed by the existing USE runtime.
It does not route, retrieve, rank, select canonical authority, generate prose,
or alter specialist behavior.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from shared_intelligence_primitives import EvidenceItem, normalize_evidence


CONTRACT_VERSION = "v1"


def normalize_documents_for_use(
    documents: Iterable[Mapping[str, Any]],
    *,
    provenance: str = "supplied",
) -> list[dict[str, Any]]:
    """Use the shared evidence transformation while preserving USE's dict shape."""
    items = normalize_evidence(documents, provenance=provenance)
    return [
        {
            "id": item.id,
            "title": item.title,
            "url": item.url,
            "text": item.text,
        }
        for item in items
        if isinstance(item, EvidenceItem)
    ]
