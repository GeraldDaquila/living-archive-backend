#!/usr/bin/env python3
"""Pre-merge integrity gate for the canonical Gold Star learning corpus."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/qa/gold_standard_registry.json"
REVIEWS = ROOT / "docs/qa/gold_star_qualitative_transfer_review.json"

REQUIRED = {
    "benchmark_id", "subsystem", "status", "runtime_transfer",
    "query", "expected_response", "known_theme", "freeze_policy",
}

def fail(message):
    raise SystemExit(f"GOLD STAR INTEGRITY FAIL: {message}")

def main():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    reviews = json.loads(REVIEWS.read_text(encoding="utf-8"))
    records = registry.get("records", [])
    entries = reviews.get("entries", [])

    ids = [r.get("benchmark_id") for r in records]
    if len(ids) != len(set(ids)):
        fail("duplicate benchmark_id in canonical registry")

    review_ids = [r.get("benchmark_id") for r in entries]
    if len(review_ids) != len(set(review_ids)):
        fail("duplicate benchmark_id in qualitative-transfer registry")

    active = [
        r for r in records
        if r.get("status") == "USER_APPROVED_GOLD_STANDARD"
        and r.get("runtime_transfer") is True
    ]

    for record in active:
        missing = sorted(k for k in REQUIRED if not record.get(k))
        if missing:
            fail(f"{record.get('benchmark_id')} missing: {', '.join(missing)}")
        if "expected_doorway" not in record and not record.get("doorway_status"):
            fail(f"{record['benchmark_id']} lacks explicit doorway state")

    active_ids = {r["benchmark_id"] for r in active}
    review_set = set(review_ids)
    missing_reviews = sorted(active_ids - review_set)
    if missing_reviews:
        fail("active Gold Stars without review: " + ", ".join(missing_reviews))

    orphan_reviews = sorted(review_set - set(ids))
    if orphan_reviews:
        fail("orphan qualitative-transfer reviews: " + ", ".join(orphan_reviews))

    approved = [
        r for r in records
        if r.get("status") == "USER_APPROVED_GOLD_STANDARD"
    ]
    if len(active) != len(approved):
        fail("not every user-approved Gold Star is active for runtime transfer")

    print(f"GOLD STAR INTEGRITY PASS: {len(active)} active contributors, {len(entries)} reviews")

if __name__ == "__main__":
    main()
