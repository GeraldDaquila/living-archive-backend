"""Audit registry permission against runtime qualitative review and renderer support.

The runtime takes deterministic eligibility from the Gold Star registry, but
reasoning_family and the structural discipline/boundary from the qualitative
transfer-review register. Join those sources by benchmark_id; never infer
runtime capability from similarly named registry fields.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict

from gold_star_deterministic_composition import _PLANS

_RUNTIME_STATUS = "USER_APPROVED_GOLD_STANDARD"


def build_capability_audit(
    registry: Dict[str, Any],
    transfer_review: Dict[str, Any],
) -> Dict[str, Any]:
    records = registry.get("records")
    entries = transfer_review.get("entries")
    if not isinstance(records, list):
        raise ValueError("registry.records must be a list")
    if not isinstance(entries, list):
        raise ValueError("transfer_review.entries must be a list")

    review_by_id = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        benchmark_id = str(entry.get("benchmark_id") or "").strip()
        if benchmark_id:
            if benchmark_id in review_by_id:
                raise ValueError(f"duplicate transfer-review benchmark_id: {benchmark_id}")
            review_by_id[benchmark_id] = entry

    eligible = [
        record for record in records
        if isinstance(record, dict)
        and isinstance(record.get("gold_star_capabilities"), dict)
        and record["gold_star_capabilities"].get("deterministic_fallback_eligible") is True
    ]
    runtime_eligible = [
        record for record in eligible
        if record.get("status") == _RUNTIME_STATUS
    ]
    superseded = [
        record for record in eligible
        if record.get("status") == "SUPERSEDED_GOLD_STANDARD"
    ]

    missing_review = [
        record for record in runtime_eligible
        if str(record.get("benchmark_id") or "").strip() not in review_by_id
    ]
    reviewed = [
        (record, review_by_id[str(record.get("benchmark_id") or "").strip()])
        for record in runtime_eligible
        if str(record.get("benchmark_id") or "").strip() in review_by_id
    ]
    missing_family = [
        (record, review) for record, review in reviewed
        if not str(review.get("reasoning_family") or "").strip()
    ]
    named = [
        (record, review) for record, review in reviewed
        if str(review.get("reasoning_family") or "").strip()
    ]
    supported = [
        (record, review) for record, review in named
        if review["reasoning_family"] in _PLANS
    ]
    unsupported = [
        (record, review) for record, review in named
        if review["reasoning_family"] not in _PLANS
    ]

    family_counts = Counter(review["reasoning_family"] for _, review in named)
    supported_families = sorted(set(family_counts).intersection(_PLANS))
    unsupported_families = sorted(set(family_counts).difference(_PLANS))

    return {
        "schema_version": 2,
        "registry_record_count": len(records),
        "review_entry_count": len(entries),
        "eligible_record_count": len(eligible),
        "superseded_eligible_record_count": len(superseded),
        "runtime_eligible_record_count": len(runtime_eligible),
        "runtime_eligible_missing_review_count": len(missing_review),
        "runtime_eligible_missing_family_count": len(missing_family),
        "runtime_eligible_named_family_record_count": len(named),
        "runtime_eligible_renderer_supported_record_count": len(supported),
        "runtime_eligible_renderer_unsupported_record_count": len(unsupported),
        "runtime_eligible_named_family_count": len(family_counts),
        "renderer_plan_count": len(_PLANS),
        "supported_families": [
            {"reasoning_family": family, "runtime_eligible_record_count": family_counts[family],
             "plan_id": _PLANS[family]["plan_id"]}
            for family in supported_families
        ],
        "unsupported_families": [
            {"reasoning_family": family, "runtime_eligible_record_count": family_counts[family]}
            for family in unsupported_families
        ],
        "missing_review_records": [
            {"benchmark_id": str(record.get("benchmark_id") or ""),
             "status": str(record.get("status") or "")}
            for record in missing_review
        ],
        "missing_family_records": [
            {"benchmark_id": str(record.get("benchmark_id") or ""),
             "reasoning_family": ""}
            for record, _ in missing_family
        ],
        "interpretation": {
            "eligible": "Registry permission only; superseded records are not active runtime lessons.",
            "runtime_eligible": "USER_APPROVED_GOLD_STANDARD records whose deterministic fallback flag is true.",
            "renderer_supported": "The joined qualitative-review reasoning family has a reviewed deterministic plan.",
            "selected_applied": "Must be established separately from runtime selection and application evidence.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path(__file__).parent / "docs/qa/gold_standard_registry.json",
    )
    parser.add_argument(
        "--review",
        type=Path,
        default=Path(__file__).parent / "docs/qa/gold_star_qualitative_transfer_review.json",
    )
    parser.add_argument("--check", action="store_true",
                        help="exit nonzero if active eligible records lack review/family/renderer support")
    args = parser.parse_args()
    report = build_capability_audit(
        json.loads(args.registry.read_text(encoding="utf-8")),
        json.loads(args.review.read_text(encoding="utf-8")),
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.check and (
        report["runtime_eligible_missing_review_count"]
        or report["runtime_eligible_missing_family_count"]
        or report["runtime_eligible_renderer_unsupported_record_count"]
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
