#!/usr/bin/env python3
"""Pre-merge integrity gate for the canonical Gold Star learning corpus."""
import json
import re
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

def normalize_exact_question(value):
    text = str(value or "").translate(str.maketrans({
        "‐": "-", "‑": "-", "‒": "-", "–": "-",
        "—": "-", "−": "-", "‘": "'", "’": "'",
        "ʼ": "'", "＇": "'",
    }))
    normalized = re.sub(r"\s+", " ", text).strip().casefold()
    return re.sub(r"[?.!]+$", "", normalized).strip()

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
        legacy = record.get("legacy_approval_grandfathered") is True
        if not legacy:
            if record.get("user_reviewed_response") is not True:
                fail(f"{record['benchmark_id']} lacks explicit evidence that the user reviewed the actual response")
            if record.get("explicit_user_elevation_approval") is not True:
                fail(f"{record['benchmark_id']} lacks explicit user authorization for Gold Star elevation")
            if not str(record.get("elevation_approval_evidence") or "").strip():
                fail(f"{record['benchmark_id']} lacks recorded elevation approval evidence")
        elif not str(record.get("legacy_approval_grandfathered_reason") or "").strip():
            fail(f"{record['benchmark_id']} has an undocumented legacy approval exemption")
        if "expected_doorway" not in record:
            fail(f"{record['benchmark_id']} lacks explicit doorway state")
        doorway = record.get("expected_doorway")
        if doorway is None:
            if record.get("doorway_status") not in {
                "INTENTIONALLY_NONE_APPROVED",
                "LEGACY_INCOMPLETE_NOT_APPROVED",
                "NOT_APPROVED_CONCEPTUAL_MISMATCH",
            }:
                fail(f"{record['benchmark_id']} has no explicit approved/withheld doorway state")
        elif (
            not isinstance(doorway, dict)
            or not str(doorway.get("title") or "").strip()
            or not str(doorway.get("url") or "").strip()
        ):
            fail(f"{record['benchmark_id']} has an incomplete expected_doorway")

    active_ids = {r["benchmark_id"] for r in active}
    review_set = set(review_ids)
    missing_reviews = sorted(active_ids - review_set)
    if missing_reviews:
        fail("active Gold Stars without review: " + ", ".join(missing_reviews))

    orphan_reviews = sorted(review_set - set(ids))
    if orphan_reviews:
        fail("orphan qualitative-transfer reviews: " + ", ".join(orphan_reviews))

    # Exact-answer authority must be unique across both active Gold Stars and
    # exact-query release candidates. Candidates are not Gold Stars and may not
    # participate in runtime learning, but they can temporarily serve a precise
    # visitor-facing answer for review. They therefore cannot compete with any
    # approved deterministic answer for the same normalized question.
    release_candidates = [
        r for r in records
        if r.get("status") == "USER_APPROVED_RELEASE_CANDIDATE"
    ]
    for candidate in release_candidates:
        if candidate.get("runtime_transfer") is not False:
            fail(f"{candidate.get('benchmark_id')} release candidate must not be runtime-transfer active")
        capabilities = candidate.get("gold_star_capabilities") or {}
        if bool(capabilities.get("active_quality_contributor")):
            fail(f"{candidate.get('benchmark_id')} release candidate cannot be an active quality contributor")
        if capabilities.get("exact_answer_authority") and candidate.get("candidate_state") != "PENDING_VISITOR_REVIEW":
            fail(f"{candidate.get('benchmark_id')} exact-query release candidate lacks pending-review state")

    exact_authority = {}
    for record in [*active, *release_candidates]:
        capabilities = record.get("gold_star_capabilities") or {}
        if not bool(capabilities.get("exact_answer_authority")):
            continue
        question = normalize_exact_question(record.get("query"))
        answer = str(record.get("expected_response") or "").strip()
        if not question or not answer:
            fail(f"{record['benchmark_id']} has incomplete exact-answer authority")
        previous = exact_authority.get(question)
        if previous:
            fail(
                "duplicate exact-answer authority for normalized question: "
                + question
            )
        exact_authority[question] = {
            "benchmark_id": record["benchmark_id"],
            "answer": answer,
        }

    approved = [
        r for r in records
        if r.get("status") == "USER_APPROVED_GOLD_STANDARD"
    ]
    if len(active) != len(approved):
        fail("not every user-approved Gold Star is active for runtime transfer")

    numbered = [r.get("gold_star_number") for r in approved if r.get("gold_star_number") is not None]
    if any(not isinstance(n, int) or n <= 0 for n in numbered):
        fail("gold_star_number must be a positive integer when present")
    if len(numbered) != len(set(numbered)):
        fail("duplicate gold_star_number in canonical registry")
    print(f"GOLD STAR INTEGRITY PASS: {len(active)} active contributors, {len(entries)} reviews, {len(numbered)} explicitly numbered records, {len(exact_authority)} exact-answer authorities")

if __name__ == "__main__":
    main()
