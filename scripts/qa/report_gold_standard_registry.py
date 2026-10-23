#!/usr/bin/env python3
"""Emit a reproducible QA identity report for the central gold-standard registry.

The caller must supply the tested application commit and runtime identity. This
script deliberately does not guess them from the registry checkout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = ROOT / "docs" / "qa" / "gold_standard_registry.json"


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
    parser.add_argument("--output", type=Path, help="Write report JSON here; stdout if omitted")
    args = parser.parse_args()

    if not args.application_commit or not args.runtime_identity:
        parser.error(
            "supply --application-commit and --runtime-identity (or "
            "QA_APPLICATION_COMMIT and QA_RUNTIME_IDENTITY); identity is never guessed"
        )

    registry_bytes = args.registry.read_bytes()
    registry = json.loads(registry_bytes)
    report = {
        "report_schema_version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "registry_id": registry["registry_id"],
        "registry_schema_version": registry["schema_version"],
        "registry_status": registry["registry_status"],
        "registry_revision": git_value("rev-parse", "HEAD"),
        "registry_file": str(args.registry.relative_to(ROOT))
        if args.registry.is_relative_to(ROOT)
        else str(args.registry),
        "registry_sha256": hashlib.sha256(registry_bytes).hexdigest(),
        "benchmark_count": len(registry["records"]),
        "benchmark_ids": [item["benchmark_id"] for item in registry["records"]],
        "application_commit": args.application_commit,
        "runtime_identity": args.runtime_identity,
        "limitations": [
            "This report identifies the registry and tested application/runtime; it does not itself assert that tests passed.",
            "A registry revision of null means the registry checkout was not inside a Git worktree or Git was unavailable.",
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
