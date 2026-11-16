#!/usr/bin/env python3
"""Fail-closed integrity gate for the canonical Gold Star learning corpus.

Numbering authority is the canonical registry on the target branch. Existing
assignments are immutable: a PR may add an assignment to a genuinely new
approved record, but may not renumber, recycle, or remove an existing one.
Descriptive audit counts are validated against record-level facts and never
used to allocate the next number.
"""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/qa/gold_standard_registry.json"
REVIEWS = ROOT / "docs/qa/gold_star_qualitative_transfer_review.json"
APPROVED_STATUS = "USER_APPROVED_GOLD_STANDARD"
BASELINE_REF = "refs/remotes/origin/main"


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


def approved_number_map(records):
    """Return stable benchmark_id -> number mappings for approved records."""
    result = {}
    for record in records:
        if record.get("status") != APPROVED_STATUS:
            continue
        number = record.get("gold_star_number")
        if number is not None:
            if isinstance(number, bool) or not isinstance(number, int) or number <= 0:
                fail(
                    f"{record.get('benchmark_id')} gold_star_number must be "
                    "a positive integer (booleans are not numbers)"
                )
            result[record["benchmark_id"]] = number
    return result


def load_json(path, label):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read {label}: {exc}")



def validate_numbering_metadata(registry, records):
    """Require explicit serial state for every approved record and explain every gap."""
    approved = [r for r in records if r.get("status") == APPROVED_STATUS]
    assigned = []
    for record in approved:
        benchmark_id = str(record.get("benchmark_id") or "<missing-id>")
        number = record.get("gold_star_number")
        state = record.get("numbering_status")
        reason_code = str(record.get("numbering_unassigned_reason_code") or "").strip()
        reason = str(record.get("numbering_unassigned_reason") or "").strip()
        if number is None:
            if state != "UNASSIGNED" or not reason_code or not reason:
                fail(f"{benchmark_id} is unnumbered but lacks explicit UNASSIGNED state/reason")
            continue
        if isinstance(number, bool) or not isinstance(number, int) or number <= 0:
            fail(f"{benchmark_id} gold_star_number must be a positive integer")
        if state != "ASSIGNED":
            fail(f"{benchmark_id} has gold_star_number #{number} but numbering_status is not ASSIGNED")
        if reason_code or reason:
            fail(f"{benchmark_id} is ASSIGNED but also carries an unassigned reason")
        assigned.append(number)

    if not assigned:
        fail("no assigned Gold Star serials exist; cannot reconcile sequence gaps")
    expected_gaps = set(range(min(assigned), max(assigned) + 1)) - set(assigned)
    gap_entries = registry.get("numbering_gap_register")
    if not isinstance(gap_entries, list):
        fail("numbering_gap_register must be an array")
    gap_numbers = []
    for gap in gap_entries:
        if not isinstance(gap, dict):
            fail("numbering_gap_register contains a non-object entry")
        number = gap.get("number")
        if isinstance(number, bool) or not isinstance(number, int) or number <= 0:
            fail("numbering gap must have a positive integer number")
        if gap.get("status") != "UNASSIGNED_HISTORICAL_GAP":
            fail(f"#{number} gap must declare UNASSIGNED_HISTORICAL_GAP")
        if not str(gap.get("reason_code") or "").strip() or not str(gap.get("reason") or "").strip():
            fail(f"#{number} gap lacks a reason code or explanation")
        if not isinstance(gap.get("evidence_checked"), list) or not gap["evidence_checked"]:
            fail(f"#{number} gap lacks an evidence-check record")
        if not str(gap.get("disposition") or "").strip():
            fail(f"#{number} gap lacks a disposition")
        gap_numbers.append(number)
    if len(gap_numbers) != len(set(gap_numbers)):
        fail("duplicate serial in numbering_gap_register")
    if set(gap_numbers) != expected_gaps:
        fail(
            "numbering_gap_register does not exactly match gaps in the assigned "
            f"serial range; expected {sorted(expected_gaps)}, got {sorted(gap_numbers)}"
        )
    if set(gap_numbers) & set(assigned):
        fail("a serial cannot be both assigned and listed as an unassigned gap")


def validate_numbering_against_base(current_records):
    """Compare the PR registry with its merge-base version from canonical main."""
    try:
        merge_base = subprocess.run(
            ["git", "merge-base", "HEAD", BASELINE_REF],
            cwd=ROOT, check=True, capture_output=True, text=True,
        ).stdout.strip()
        if not merge_base:
            fail("cannot resolve merge base with origin/main")
        base_text = subprocess.run(
            ["git", "show", f"{merge_base}:docs/qa/gold_standard_registry.json"],
            cwd=ROOT, check=True, capture_output=True, text=True,
        ).stdout
        base_registry = json.loads(base_text)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        fail(f"cannot load canonical base registry for immutable-number check: {exc}")

    base_records = base_registry.get("records", [])
    base_ids = {r.get("benchmark_id") for r in base_records}
    base_numbers = approved_number_map(base_records)
    current_numbers = approved_number_map(current_records)

    # Existing Gold Star IDs cannot disappear, be demoted, or have their number
    # removed/changed in a proposed branch.
    current_approved = {
        r.get("benchmark_id"): r
        for r in current_records
        if r.get("status") == APPROVED_STATUS
    }
    base_approved = {
        r.get("benchmark_id"): r
        for r in base_records
        if r.get("status") == APPROVED_STATUS
    }

    disappeared = sorted(set(base_approved) - set(current_approved))
    if disappeared:
        fail("existing approved Gold Stars removed/demoted from canonical base: "
             + ", ".join(disappeared))

    changed = []
    for benchmark_id, base_number in base_numbers.items():
        current_number = current_numbers.get(benchmark_id)
        if current_number != base_number:
            changed.append(
                f"{benchmark_id} ({base_number} -> "
                f"{current_number if current_number is not None else 'UNASSIGNED'})"
            )
    if changed:
        fail("existing Gold Star number assignment changed: " + "; ".join(changed))

    # Existing unnumbered approved records cannot receive inferred numbers.
    # A numbered migration is permitted only when the record carries explicit,
    # user-authorized migration evidence and the allocation remains contiguous.
    current_by_id = {r.get("benchmark_id"): r for r in current_records}
    retroactive = sorted(
        benchmark_id for benchmark_id in current_numbers
        if benchmark_id in base_ids and benchmark_id not in base_numbers
    )
    unauthorized_migrations = []
    for benchmark_id in retroactive:
        record = current_by_id.get(benchmark_id, {})
        migration = record.get("numbering_migration")
        if not isinstance(migration, dict):
            unauthorized_migrations.append(benchmark_id)
            continue
        required = {
            "authority", "approved_at", "reason",
            "previous_numbering_state", "migration_class",
        }
        missing = [key for key in sorted(required) if not str(migration.get(key) or "").strip()]
        if (
            migration.get("migration_class") != "explicit_user_authorized_numbering_migration"
            or migration.get("previous_numbering_state") != "approved_unnumbered"
            or missing
        ):
            unauthorized_migrations.append(benchmark_id)
    if unauthorized_migrations:
        fail("existing approved records cannot receive inferred/retroactive numbers "
             "without an explicit authorized numbering migration: "
             + ", ".join(unauthorized_migrations))

    # New assignments must be contiguous after the highest number already
    # present on main; gaps in historical sequences remain untouched.
    base_max = max(base_numbers.values(), default=0)
    new_assignments = sorted(
        number for benchmark_id, number in current_numbers.items()
        if benchmark_id not in base_numbers
    )
    if new_assignments:
        expected = list(range(base_max + 1, base_max + 1 + len(new_assignments)))
        if new_assignments != expected:
            fail(
                "new Gold Star numbers must be allocated contiguously after "
                f"canonical main max #{base_max}; expected {expected}, got {new_assignments}"
            )

    # Ensure numbers are unique across all current approved records.
    number_to_ids = {}
    for benchmark_id, number in current_numbers.items():
        number_to_ids.setdefault(number, []).append(benchmark_id)
    collisions = {
        number: ids for number, ids in number_to_ids.items() if len(ids) > 1
    }
    if collisions:
        fail("duplicate Gold Star number assignments: "
             + "; ".join(f"#{n}: {', '.join(ids)}" for n, ids in sorted(collisions.items())))

    return base_numbers, current_numbers


def main():
    registry = load_json(REGISTRY, "canonical registry")
    reviews = load_json(REVIEWS, "qualitative-transfer registry")
    records = registry.get("records", [])
    entries = reviews.get("entries", [])

    if not isinstance(records, list) or not isinstance(entries, list):
        fail("registry records and review entries must be arrays")

    ids = [r.get("benchmark_id") for r in records]
    if any(not value for value in ids):
        fail("every registry record must have a benchmark_id")
    if len(ids) != len(set(ids)):
        fail("duplicate benchmark_id in canonical registry")

    review_ids = [r.get("benchmark_id") for r in entries]
    if any(not value for value in review_ids):
        fail("every qualitative-transfer review must have a benchmark_id")
    if len(review_ids) != len(set(review_ids)):
        fail("duplicate benchmark_id in qualitative-transfer registry")

    active = [
        r for r in records
        if r.get("status") == APPROVED_STATUS
        and r.get("runtime_transfer") is True
    ]

    for record in active:
        legacy = record.get("legacy_approval_grandfathered") is True
        required_text = {
            "benchmark_id", "subsystem", "query", "expected_response",
            "known_theme", "freeze_policy",
        }
        missing = sorted(k for k in required_text if not str(record.get(k) or "").strip())
        if missing:
            fail(f"{record.get('benchmark_id')} missing required Gold Star metadata: {', '.join(missing)}")
        rating = record.get("rating_out_of_10", record.get("rating"))
        if rating is not None and (not isinstance(rating, (int, float)) or isinstance(rating, bool)):
            fail(f"{record['benchmark_id']} has an invalid rating")
        if not legacy and rating is None:
            fail(f"{record['benchmark_id']} lacks a numeric rating")
        if not isinstance(record.get("gold_star_capabilities"), dict) or record["gold_star_capabilities"].get("active_quality_contributor") is not True:
            fail(f"{record['benchmark_id']} lacks active quality-contributor authority")

        if legacy:
            legacy_reason = str(record.get("legacy_approval_grandfathered_reason") or "").strip()
            if not legacy_reason:
                fail(f"{record['benchmark_id']} has an undocumented legacy approval exemption")
            # Explicit legacy exemption preserves earlier approvals without
            # inventing reconstructed approval-state dates or reviewer text.
        else:
            modern_required = {
                "approval_state", "elevation_approval_evidence", "reasoning_family",
                "transferable_lesson", "transfer_boundary", "user_approved_at",
            }
            modern_missing = sorted(k for k in modern_required if not str(record.get(k) or "").strip())
            if modern_missing:
                fail(f"{record['benchmark_id']} missing modern approval metadata: {', '.join(modern_missing)}")
            if record.get("user_reviewed_response") is not True:
                fail(f"{record['benchmark_id']} lacks explicit evidence that the user reviewed the actual response")
            if record.get("explicit_user_elevation_approval") is not True:
                fail(f"{record['benchmark_id']} lacks explicit user authorization for Gold Star elevation")

        provenance = record.get("provenance")
        if not isinstance(provenance, dict):
            fail(f"{record['benchmark_id']} lacks a provenance object")
        if legacy:
            # Older records may not contain the later structured source fields.
            # Their documented legacy approval reason is the explicit exemption;
            # do not fabricate source dates or reviewer evidence.
            if not str(provenance.get("source") or provenance.get("evidence") or record.get("legacy_approval_grandfathered_reason") or "").strip():
                fail(f"{record['benchmark_id']} lacks legacy provenance evidence")
            if not str(record.get("legacy_approval_grandfathered_reason") or "").strip():
                fail(f"{record['benchmark_id']} lacks the required legacy approval exception reason")
        else:
            if not str(provenance.get("source") or "").strip():
                fail(f"{record['benchmark_id']} lacks provenance.source")
            if not str(provenance.get("source_date") or provenance.get("approved_at") or "").strip():
                fail(f"{record['benchmark_id']} lacks provenance date")
            if not str(provenance.get("evidence_boundary") or record.get("transfer_boundary") or "").strip():
                fail(f"{record['benchmark_id']} lacks a provenance/evidence boundary")

        assertions = record.get("assertions")
        if not isinstance(assertions, list) or not assertions or any(not str(x).strip() for x in assertions):
            fail(f"{record['benchmark_id']} lacks non-empty acceptance assertions")
        freeze_policy = str(record.get("freeze_policy") or "").strip()
        if legacy:
            if not freeze_policy:
                fail(f"{record['benchmark_id']} lacks its recorded legacy freeze policy")
        elif freeze_policy not in {
            "immutable_user_approved_gold_standard",
            "Preserve approved expected_response. Change only with explicit user authorization and a separately documented benchmark-version change.",
        }:
            fail(f"{record['benchmark_id']} is not frozen under a recognized immutable approval policy")

        if "expected_doorway" not in record:
            fail(f"{record['benchmark_id']} lacks explicit doorway state")
        doorway = record.get("expected_doorway")
        doorway_status = str(record.get("doorway_status") or "").strip()
        withheld_states = {
            "INTENTIONALLY_NONE_APPROVED",
            "LEGACY_INCOMPLETE_NOT_APPROVED",
            "NOT_APPROVED_CONCEPTUAL_MISMATCH",
        }
        if doorway is None:
            if doorway_status not in withheld_states:
                fail(f"{record['benchmark_id']} has no explicit approved/withheld doorway state")
        else:
            if doorway_status == "INTENTIONALLY_NONE_APPROVED":
                fail(
                    f"{record['benchmark_id']} declares INTENTIONALLY_NONE_APPROVED "
                    "but also contains an expected_doorway"
                )
            if (
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

    exact_authority = {}
    for record in active:
        capabilities = record.get("gold_star_capabilities") or {}
        if not bool(capabilities.get("exact_answer_authority")):
            continue
        question = normalize_exact_question(record.get("query"))
        answer = str(record.get("expected_response") or "").strip()
        if not question or not answer:
            fail(f"{record['benchmark_id']} has incomplete exact-answer authority")
        previous = exact_authority.get(question)
        if previous and previous["answer"] != answer:
            fail("conflicting exact-answer authority for normalized question: " + question)
        exact_authority[question] = {
            "benchmark_id": record["benchmark_id"],
            "answer": answer,
        }

    approved = [r for r in records if r.get("status") == APPROVED_STATUS]
    if len(active) != len(approved):
        fail("not every user-approved Gold Star is active for runtime transfer")

    validate_numbering_metadata(registry, records)
    base_numbers, current_numbers = validate_numbering_against_base(records)

    # Audit metadata is descriptive only. When present, it must match the
    # record-level inventory; it is never consulted to select a number.
    audit = registry.get("integrity_audit") or {}
    expected_audit = {
        "approved_gold_star_count": len(approved),
        "registry_record_count": len(records),
        "numbered_gold_star_record_count": len(current_numbers),
        "highest_assigned_gold_star_number": max(current_numbers.values(), default=0),
        "unassigned_approved_gold_star_count": sum(1 for r in approved if r.get("gold_star_number") is None),
        "documented_numbering_gap_count": len(registry.get("numbering_gap_register") or []),
    }
    for key, actual in expected_audit.items():
        declared = audit.get(key)
        if declared != actual:
            fail(f"integrity_audit.{key} is {declared!r}; record-level value is {actual}")

    print(
        "GOLD STAR INTEGRITY PASS: "
        f"{len(approved)} approved, {len(records)} total records, "
        f"{len(current_numbers)} numbered, max #{max(current_numbers.values(), default=0)}, "
        f"{len(entries)} reviews, {len(exact_authority)} exact-answer authorities; "
        "canonical-main assignment immutability PASS"
    )


if __name__ == "__main__":
    main()
