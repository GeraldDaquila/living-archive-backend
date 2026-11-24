#!/usr/bin/env python3
"""Emit a reproducible, dynamically derived Gold Star inventory report.

The canonical registry is the sole source of live counts. Historical audit
counters are retained for provenance but are reported only as metadata drift.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = ROOT / "docs" / "qa" / "gold_standard_registry.json"
DEFAULT_REVIEW = ROOT / "docs" / "qa" / "gold_star_qualitative_transfer_review.json"
DEFAULT_TRANSFER_MAP = ROOT / "docs" / "qa" / "gold_star_transferability_map.json"
sys.path.insert(0, str(ROOT))
from gold_star_inventory import derive_gold_star_inventory  # noqa: E402


def git_value(*args: str) -> str | None:
    try:
        value = subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
        return value or None
    except (OSError, subprocess.CalledProcessError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--application-commit", default=os.getenv("QA_APPLICATION_COMMIT"))
    parser.add_argument("--runtime-identity", default=os.getenv("QA_RUNTIME_IDENTITY"))
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--transfer-map", type=Path, default=DEFAULT_TRANSFER_MAP)
    parser.add_argument("--output", type=Path, help="Write report JSON here; stdout if omitted")
    args = parser.parse_args()

    if not args.application_commit or not args.runtime_identity:
        parser.error(
            "supply --application-commit and --runtime-identity (or "
            "QA_APPLICATION_COMMIT and QA_RUNTIME_IDENTITY); identity is never guessed"
        )

    registry_bytes = args.registry.read_bytes()
    registry = json.loads(registry_bytes)
    review = json.loads(args.review.read_text(encoding="utf-8")) if args.review.exists() else {}
    transfer_map = (
        json.loads(args.transfer_map.read_text(encoding="utf-8"))
        if args.transfer_map.exists() else {}
    )
    inventory = derive_gold_star_inventory(registry, review, transfer_map)
    report = {
        "report_schema_version": "2.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "registry_id": registry["registry_id"],
        "registry_schema_version": registry["schema_version"],
        "registry_status": registry["registry_status"],
        "registry_revision": git_value("rev-parse", "HEAD"),
        "registry_file": str(args.registry.relative_to(ROOT))
        if args.registry.is_relative_to(ROOT) else str(args.registry),
        "registry_sha256": hashlib.sha256(registry_bytes).hexdigest(),
        "application_commit": args.application_commit,
        "runtime_identity": args.runtime_identity,
        "inventory": inventory,
        # Backward-compatible top-level fields are aliases of derived values.
        "benchmark_count": inventory["benchmark_count"],
        "authoritative_gold_star_count": inventory["approved_gold_star_count"],
        "active_runtime_gold_star_count": inventory["active_runtime_gold_star_count"],
        "exact_query_only_successor_count": inventory["exact_query_only_successor_count"],
        "superseded_historical_reference_count": inventory["superseded_historical_reference_count"],
        "approved_response_quality_exemplar_count": inventory["approved_response_quality_exemplar_count"],
        "pending_approval_evidence_count": inventory["pending_approval_evidence_count"],
        "counting_note": inventory["counting_note"],
        "numbered_gold_star_count": inventory["numbered_gold_star_count"],
        "unassigned_approved_gold_star_count": inventory["unassigned_approved_gold_star_count"],
        "highest_assigned_gold_star_number": inventory["highest_assigned_gold_star_number"],
        "numbering_sequence_start": registry.get("numbering_policy", {}).get("sequence_start"),
        "numbering_gap_register": registry.get("numbering_gap_register", []),
        "number_assignments": inventory["number_assignments"],
        "unassigned_benchmark_ids": inventory["unassigned_benchmark_ids"],
        "limitations": [
            "This report identifies the registry and tested application/runtime; it does not itself assert that tests passed.",
            "A registry revision of null means the registry checkout was not inside a Git worktree or Git was unavailable.",
            "Live counts are derived from canonical records; legacy audit metadata drift is informational and does not override derived counts.",
        ],
    }
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
