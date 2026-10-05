"""Guide Node Registry — draft structural contract for The Guide.

This module is intentionally structural, not intelligent.

WordPress owns the canonical navigation and approved node records.
The Guide/USE consumes the records and decides whether a visitor's
question warrants a native node handoff.

No embeddings, LLM calls, crawling, content duplication, or specialist
logic belong here.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse


GUIDE_NODE_REGISTRY_VERSION = "v1"
GUIDE_NODE_SCHEMA_VERSION = "v1"


@dataclass(frozen=True)
class GuideNode:
    node_id: str
    title: str
    branch: str
    parent: str
    purpose: str
    asset_type: str
    canonical_url: str
    access_class: str
    status: str = "active"
    menu_depth: int = 0
    discovery_priority: str = "normal"
    semantic_hints: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["semantic_hints"] = list(self.semantic_hints)
        return payload


def _is_public_archive_url(value: str) -> bool:
    try:
        parsed = urlparse(str(value).strip())
    except Exception:
        return False
    return (
        parsed.scheme == "https"
        and parsed.netloc.lower() == "geralddaquila.com"
        and bool(parsed.path)
    )


def validate_node(record: Mapping[str, Any]) -> list[str]:
    """Return validation errors without mutating the supplied record."""
    errors: list[str] = []
    required = (
        "node_id",
        "title",
        "branch",
        "purpose",
        "asset_type",
        "canonical_url",
        "access_class",
        "status",
    )
    for field in required:
        if not str(record.get(field) or "").strip():
            errors.append(f"missing:{field}")

    if record.get("status") not in {"active", "candidate", "disabled"}:
        errors.append("invalid:status")

    if record.get("access_class") not in {
        "public",
        "steward",
        "protected",
        "purchase",
        "mixed",
    }:
        errors.append("invalid:access_class")

    if record.get("canonical_url") and not _is_public_archive_url(
        str(record["canonical_url"])
    ):
        errors.append("invalid:canonical_url")

    try:
        depth = int(record.get("menu_depth", 0))
        if depth < 0:
            errors.append("invalid:menu_depth")
    except (TypeError, ValueError):
        errors.append("invalid:menu_depth")

    return errors


def validate_registry(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate the registry and return a bounded QA report."""
    seen: set[str] = set()
    valid = 0
    errors: list[dict[str, Any]] = []

    for record in records:
        node_id = str(record.get("node_id") or "").strip()
        if node_id in seen:
            errors.append({"node_id": node_id, "errors": ["duplicate:node_id"]})
            continue
        seen.add(node_id)

        node_errors = validate_node(record)
        if node_errors:
            errors.append({"node_id": node_id, "errors": node_errors})
        else:
            valid += 1

    return {
        "registry_version": GUIDE_NODE_REGISTRY_VERSION,
        "schema_version": GUIDE_NODE_SCHEMA_VERSION,
        "total": len(seen),
        "valid": valid,
        "invalid": len(errors),
        "errors": errors,
    }


def active_nodes(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return only explicitly approved, active Guide Nodes."""
    output: list[dict[str, Any]] = []
    for record in records:
        if str(record.get("status") or "").strip() != "active":
            continue
        if validate_node(record):
            continue
        output.append(dict(record))
    return output


def node_handoff_payload(
    node: Mapping[str, Any],
    *,
    query: str,
    request_id: str,
    visitor_boundary_version: str,
) -> dict[str, Any]:
    """Build the common native-node handoff envelope.

    This does not decide whether a node is appropriate. That decision belongs
    to the Guide's existing intent/routing layer.
    """
    errors = validate_node(node)
    if errors:
        raise ValueError(f"invalid Guide Node: {errors}")

    if node.get("status") != "active":
        raise ValueError("Guide Node is not active")

    return {
        "ok": True,
        "intent": "GUIDE_NODE_HANDOFF",
        "response": "",
        "handoff": "guide_node",
        "handoff_mode": "direct",
        "handoff_pending": True,
        "guide_node_id": node["node_id"],
        "guide_node_title": node["title"],
        "guide_node_url": node["canonical_url"],
        "guide_node_access_class": node["access_class"],
        "query": query,
        "request_id": request_id,
        "return_mode": "native_guide_node",
        "visitor_boundary_version": visitor_boundary_version,
        "guide_node_registry_version": GUIDE_NODE_REGISTRY_VERSION,
    }


__all__ = [
    "GUIDE_NODE_REGISTRY_VERSION",
    "GUIDE_NODE_SCHEMA_VERSION",
    "GuideNode",
    "active_nodes",
    "node_handoff_payload",
    "validate_node",
    "validate_registry",
]
