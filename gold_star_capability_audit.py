"""Audit registry eligibility against reviewed deterministic renderer support.

Registry eligibility is not renderer capability. This report keeps record-level
states separate and deliberately does not mutate registry authority flags.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable

from gold_star_deterministic_composition import _PLANS


def build_capability_audit(registry: Dict[str, Any]) -> Dict[str, Any]:
    records = registry.get("records")
    if not isinstance(records, list):
        raise ValueError("registry.records must be a list")

    eligible = [
        record for record in records
        if isinstance(record, dict)
        and record.get("gold_star_capabilities", {}).get(
            "deterministic_fallback_eligible"
        ) is True
    ]
    missing_family = [
        record for record in eligible
        if not str(record.get("reasoning_family") or "").strip()
    ]
    named = [
        record for record in eligible
        if str(record.get("reasoning_family") or "").strip()
    ]
    supported = [
        record for record in named
        if record["reasoning_family"] in _PLANS
    ]
    unsupported = [
        record for record in named
        if record["reasoning_family"] not in _PLANS
    ]

    family_counts = Counter(record["reasoning_family"] for record in named)
    supported_families = sorted(set(family_counts).intersection(_PLANS))
    unsupported_families = sorted(set(family_counts).difference(_PLANS))

    return {
        "schema_version": 1,
        "registry_record_count": len(records),
        "eligible_record_count": len(eligible),
        "eligible_missing_family_count": len(missing_family),
        "eligible_named_family_record_count": len(named),
        "eligible_renderer_supported_record_count": len(supported),
        "eligible_renderer_unsupported_record_count": len(unsupported),
        "eligible_named_family_count": len(family_counts),
        "renderer_plan_count": len(_PLANS),
        "supported_families": [
            {"reasoning_family": family, "eligible_record_count": family_counts[family],
             "plan_id": _PLANS[family]["plan_id"]}
            for family in supported_families
        ],
        "unsupported_families": [
            {"reasoning_family": family, "eligible_record_count": family_counts[family]}
            for family in unsupported_families
        ],
        "missing_family_records": [
            {"benchmark_id": str(record.get("benchmark_id") or ""),
             "title": str(record.get("title") or "")}
            for record in missing_family
        ],
        "interpretation": {
            "eligible": "Registry permission only; not proof of renderer support or runtime application.",
            "renderer_supported": "The reasoning family has a reviewed deterministic plan.",
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
    parser.add_argument("--check", action="store_true",
                        help="exit nonzero if eligible records lack a family or renderer plan")
    args = parser.parse_args()
    report = build_capability_audit(json.loads(args.registry.read_text(encoding="utf-8")))
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.check and (
        report["eligible_missing_family_count"]
        or report["eligible_renderer_unsupported_record_count"]
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
