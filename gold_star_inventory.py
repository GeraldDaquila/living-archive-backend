"""Derive live Gold Star inventory from canonical records, never fixed totals.

The registry records are the source of truth. Counts are observations, not
configuration. Historical audit counters are reported as drift only; they do
not override or constrain the live inventory.
"""
from __future__ import annotations

from collections import Counter
from typing import Any


APPROVED = "USER_APPROVED_GOLD_STANDARD"
ACTIVE_SUBSYSTEM = "general-purpose-guide"
PENDING_APPROVAL = "RECOVERED_HISTORICAL_RESPONSE_PENDING_APPROVAL_EVIDENCE"


def _records(value: Any) -> list[dict]:
    return [item for item in value or [] if isinstance(item, dict)]


def _ids(items: list[dict]) -> list[str]:
    return [str(item.get("benchmark_id") or "").strip() for item in items]


def derive_gold_star_inventory(
    registry: dict,
    review: dict | None = None,
    transfer_map: dict | None = None,
) -> dict:
    """Return live counts and set reconciliation derived from source records."""
    records = _records(registry.get("records"))
    approved = [r for r in records if r.get("status") == APPROVED]
    active = [r for r in approved if r.get("runtime_transfer") is True]
    exact_only = [
        r for r in approved
        if r.get("runtime_transfer") is False
        and not r.get("superseded_by_benchmark_id")
        and (r.get("gold_star_capabilities") or {}).get("generation_class")
        != "user_approved_response_quality_exemplar"
    ]
    superseded = [r for r in approved if r.get("superseded_by_benchmark_id")]
    exemplars = [
        r for r in approved
        if (r.get("gold_star_capabilities") or {}).get("generation_class")
        == "user_approved_response_quality_exemplar"
    ]
    pending = [r for r in records if r.get("status") == PENDING_APPROVAL]
    numbered = [
        r for r in approved
        if r.get("numbering_status") == "ASSIGNED"
        and isinstance(r.get("gold_star_number"), int)
        and not isinstance(r.get("gold_star_number"), bool)
    ]
    unassigned = [
        r for r in approved if r.get("numbering_status") == "UNASSIGNED"
    ]

    review_entries = _records((review or {}).get("entries"))
    review_ids = _ids(review_entries)
    active_ids = set(_ids(active))
    review_id_set = set(review_ids)

    general_active = [
        r for r in active if r.get("subsystem") == ACTIVE_SUBSYSTEM
    ]
    map_entries = _records((transfer_map or {}).get("entries"))
    map_ids = _ids(map_entries)
    general_ids = set(_ids(general_active))
    map_id_set = set(map_ids)

    duplicate_ids = sorted({
        item for item, count in Counter(_ids(records)).items()
        if not item or count > 1
    })
    audit = registry.get("integrity_audit") or {}
    derived = {
        "approved_gold_star_count": len(approved),
        "registry_record_count": len(records),
        "active_quality_contributor_count": len(active),
        "numbered_gold_star_record_count": len(numbered),
        "unassigned_approved_gold_star_count": len(unassigned),
    }
    legacy_drift = {
        key: {"stored": audit[key], "derived": value}
        for key, value in derived.items()
        if key in audit and audit[key] != value
    }

    return {
        "benchmark_count": len(records),
        "status_counts": dict(sorted(Counter(
            str(r.get("status") or "MISSING_STATUS") for r in records
        ).items())),
        "approved_gold_star_count": len(approved),
        "active_runtime_gold_star_count": len(active),
        "exact_query_only_successor_count": len(exact_only),
        "superseded_historical_reference_count": len(superseded),
        "approved_response_quality_exemplar_count": len(exemplars),
        "pending_approval_evidence_count": len(pending),
        "diagnostic_record_count": sum(
            1 for r in records
            if r.get("status") in {
                "RECOVERED_REGRESSION_SCENARIO",
                "RECOVERED_DIAGNOSTIC_FIXTURE_NOT_GOLD_STANDARD",
                "RECOVERED_SHADOW_DIAGNOSTIC_NOT_GOLD_STANDARD",
            }
        ),
        "numbered_gold_star_count": len(numbered),
        "unassigned_approved_gold_star_count": len(unassigned),
        "highest_assigned_gold_star_number": max(
            (r["gold_star_number"] for r in numbered), default=None
        ),
        "number_assignments": {
            r["benchmark_id"]: r["gold_star_number"]
            for r in numbered
        },
        "unassigned_benchmark_ids": [
            r["benchmark_id"] for r in unassigned
        ],
        "qualitative_review_entry_count": len(review_entries),
        "qualitative_review_missing_ids": sorted(active_ids - review_id_set),
        "qualitative_review_orphan_ids": sorted(review_id_set - active_ids),
        "qualitative_review_duplicate_ids": sorted({
            item for item, count in Counter(review_ids).items() if count > 1
        }),
        "general_purpose_runtime_transfer_count": len(general_active),
        "transferability_map_entry_count": len(map_entries),
        "transferability_map_missing_ids": sorted(general_ids - map_id_set),
        "transferability_map_orphan_ids": sorted(map_id_set - general_ids),
        "transferability_map_duplicate_ids": sorted({
            item for item, count in Counter(map_ids).items() if count > 1
        }),
        "duplicate_or_missing_benchmark_ids": duplicate_ids,
        "legacy_audit_metadata_drift": legacy_drift,
        "counting_note": (
            "All live counts are derived from canonical registry records. "
            "Pending approval evidence and diagnostic records are reported "
            "separately and are not counted as approved Gold Stars. Historical "
            "integrity_audit counters are non-authoritative snapshots; any "
            "difference is surfaced as legacy_audit_metadata_drift."
        ),
    }
