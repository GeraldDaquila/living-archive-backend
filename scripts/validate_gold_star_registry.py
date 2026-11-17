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



def validate_exact_only_successors(approved_records, active_records):
    """Allow only explicitly bounded successors that own exact-query authority, not learning transfer."""
    active_by_id = {item.get("benchmark_id"): item for item in active_records}
    exact_only = []
    for record in approved_records:
        if record.get("runtime_transfer") is True:
            continue
        capabilities = record.get("gold_star_capabilities")
        successor_of = str(record.get("replaces_exact_query_runtime_authority_of") or "").strip()
        predecessor = active_by_id.get(successor_of)
        valid = (
            record.get("runtime_transfer") is False
            and isinstance(capabilities, dict)
            and capabilities.get("exact_answer_authority") is True
            and capabilities.get("active_quality_contributor") is False
            and capabilities.get("deterministic_fallback_eligible") is False
            and bool(successor_of)
            and isinstance(predecessor, dict)
            and predecessor.get("runtime_exact_query_successor") == record.get("benchmark_id")
            and normalize_exact_question(predecessor.get("query"))
                == normalize_exact_question(record.get("query"))
        )
        if not valid:
            fail(
                f"{record.get('benchmark_id')} is approved but neither an active "
                "quality contributor nor a valid exact-query-only successor"
            )
        exact_only.append(record)
    return exact_only


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
        recovery = record.get("numbering_recovery")
        if recovery is not None:
            required_recovery = {
                "recovery_class", "recovered_number", "source_pr", "source_pr_url",
                "source_merge_commit", "previous_registry_state", "authority_basis",
                "recovered_at",
            }
            if not isinstance(recovery, dict) or any(
                not str(recovery.get(key) or "").strip() for key in required_recovery
            ):
                fail(f"{benchmark_id} has incomplete historical numbering recovery evidence")
            if recovery.get("recovered_number") != number:
                fail(f"{benchmark_id} recovered number does not match gold_star_number")
            if recovery.get("recovery_class") not in {
                "HISTORICAL_SEQUENCE_ASSIGNMENT_RECOVERY",
                "HISTORICAL_EXPLICIT_ASSIGNMENT_RECOVERY",
            }:
                fail(f"{benchmark_id} has an unrecognized numbering recovery class")
            if isinstance(recovery.get("source_pr"), bool) or not isinstance(recovery.get("source_pr"), int):
                fail(f"{benchmark_id} numbering recovery source_pr must be an integer")
        assigned.append(number)

    if not assigned:
        fail("no assigned Gold Star serials exist; cannot reconcile sequence gaps")
    numbering_policy = registry.get("numbering_policy")
    sequence_start = numbering_policy.get("sequence_start") if isinstance(numbering_policy, dict) else None
    if isinstance(sequence_start, bool) or not isinstance(sequence_start, int) or sequence_start <= 0:
        fail("numbering_policy.sequence_start must be a positive integer")
    if min(assigned) != sequence_start:
        fail(f"numbering sequence_start #{sequence_start} does not match lowest assigned serial #{min(assigned)}")
    expected_gaps = set(range(sequence_start, max(assigned) + 1)) - set(assigned)
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
        status = gap.get("status")
        if status not in {"UNASSIGNED_HISTORICAL_GAP", "RELEASED_FOR_FUTURE_ALLOCATION"}:
            fail(f"#{number} gap must declare a recognized historical-gap status")
        if not str(gap.get("reason_code") or "").strip() or not str(gap.get("reason") or "").strip():
            fail(f"#{number} gap lacks a reason code or explanation")
        if status == "RELEASED_FOR_FUTURE_ALLOCATION":
            authorization = gap.get("release_authorization")
            if (
                number not in {85, 86}
                or not isinstance(authorization, dict)
                or authorization.get("authorization_type") != "EXPLICIT_USER_AUTHORIZED_HISTORICAL_GAP_RELEASE"
                or authorization.get("approved_by") != "user"
                or authorization.get("approved_at") != "2026-11-16"
                or not str(authorization.get("authority") or "").strip()
                or not str(authorization.get("allocation_rule") or "").strip()
                or authorization.get("historical_evidence_preserved") is not True
            ):
                fail(f"#{number} released gap lacks the narrowly authorized #85/#86 exception record")
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


def validate_numbering_against_base(current_records, current_registry=None):
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
    current_by_id_for_withdrawal = {r.get("benchmark_id"): r for r in current_records}
    unauthorized_withdrawals = []
    for benchmark_id in disappeared:
        record = current_by_id_for_withdrawal.get(benchmark_id, {})
        withdrawal = record.get("withdrawal")
        capabilities = record.get("gold_star_capabilities")
        explicitly_withdrawn = (
            record.get("status") == "WITHDRAWN_PENDING_DOORWAY"
            and isinstance(withdrawal, dict)
            and withdrawal.get("withdrawn_by_user") is True
            and bool(str(withdrawal.get("withdrawn_at") or "").strip())
            and bool(str(withdrawal.get("reason") or "").strip())
            and record.get("runtime_transfer") is False
            and isinstance(capabilities, dict)
            and capabilities.get("exact_answer_authority") is False
            and capabilities.get("active_quality_contributor") is False
            and capabilities.get("deterministic_fallback_eligible") is False
            and base_approved[benchmark_id].get("gold_star_number") is None
        )
        if not explicitly_withdrawn:
            unauthorized_withdrawals.append(benchmark_id)
    if unauthorized_withdrawals:
        fail("existing approved Gold Stars removed/demoted without explicit, fail-closed user withdrawal evidence: "
             + ", ".join(unauthorized_withdrawals))

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

    # Once merged, historical recovery evidence and gap dispositions are
    # immutable. A future branch may add a new gap only through a separate,
    # evidence-backed migration; it may not silently rewrite existing history.
    base_by_id = {r.get("benchmark_id"): r for r in base_records}
    current_by_id_for_history = {r.get("benchmark_id"): r for r in current_records}
    changed_recoveries = []
    for benchmark_id, base_record in base_by_id.items():
        base_recovery = base_record.get("numbering_recovery")
        if base_recovery is None:
            continue
        current_record = current_by_id_for_history.get(benchmark_id, {})
        if current_record.get("numbering_recovery") != base_recovery:
            changed_recoveries.append(benchmark_id)
    if changed_recoveries:
        fail("historical numbering recovery evidence is immutable: " + ", ".join(sorted(changed_recoveries)))

    if current_registry is not None:
        base_gaps = base_registry.get("numbering_gap_register")
        current_gaps = current_registry.get("numbering_gap_register")
        if isinstance(base_gaps, list):
            base_gap_map = {item.get("number"): item for item in base_gaps if isinstance(item, dict)}
            current_gap_map = {item.get("number"): item for item in (current_gaps or []) if isinstance(item, dict)}
            changed_gaps = []
            for number, base_gap in base_gap_map.items():
                current_gap = current_gap_map.get(number)
                if current_gap == base_gap:
                    continue
                # The only permitted historical-gap mutation is the explicit,
                # user-authorized release of #85 and #86. Preserve all original
                # evidence fields; add only the release authorization and its
                # resulting status/disposition.
                allowed = (
                    number in {85, 86}
                    and isinstance(current_gap, dict)
                    and current_gap.get("status") == "RELEASED_FOR_FUTURE_ALLOCATION"
                    and current_gap.get("reason_code") == base_gap.get("reason_code")
                    and current_gap.get("reason") == base_gap.get("reason")
                    and current_gap.get("evidence_checked") == base_gap.get("evidence_checked")
                    and isinstance(current_gap.get("disposition"), str)
                    and isinstance(current_gap.get("release_authorization"), dict)
                    and current_gap.get("release_authorization", {}).get("authorization_type")
                        == "EXPLICIT_USER_AUTHORIZED_HISTORICAL_GAP_RELEASE"
                    and current_gap.get("release_authorization", {}).get("approved_by") == "user"
                    and current_gap.get("release_authorization", {}).get("approved_at") == "2026-11-16"
                    and current_gap.get("release_authorization", {}).get("historical_evidence_preserved") is True
                )
                if not allowed:
                    changed_gaps.append(number)
            if changed_gaps:
                fail("historical numbering gap evidence/disposition is immutable except for the explicit #85/#86 release: "
                     + ", ".join(f"#{number}" for number in sorted(changed_gaps)))
        base_policy = base_registry.get("numbering_policy")
        current_policy = current_registry.get("numbering_policy")
        if isinstance(base_policy, dict):
            if not isinstance(current_policy, dict) or current_policy.get("sequence_start") != base_policy.get("sequence_start"):
                fail("numbering sequence_start is immutable once established on canonical main")

    # Existing unnumbered approved records cannot receive inferred numbers.
    # A numbered migration is permitted only when the record carries explicit,
    # user-authorized migration evidence and the allocation remains contiguous.
    current_by_id = {r.get("benchmark_id"): r for r in current_records}
    retroactive = sorted(
        benchmark_id for benchmark_id in current_numbers
        if benchmark_id in base_ids and benchmark_id not in base_numbers
    )
    unauthorized_migrations = []
    recovered_historical_ids = set()
    for benchmark_id in retroactive:
        record = current_by_id.get(benchmark_id, {})
        recovery = record.get("numbering_recovery")
        if isinstance(recovery, dict):
            required_recovery = {
                "recovery_class", "recovered_number", "source_pr", "source_pr_url",
                "source_merge_commit", "previous_registry_state", "authority_basis",
                "recovered_at",
            }
            missing = [key for key in sorted(required_recovery) if not str(recovery.get(key) or "").strip()]
            if (
                recovery.get("recovery_class") not in {
                    "HISTORICAL_SEQUENCE_ASSIGNMENT_RECOVERY",
                    "HISTORICAL_EXPLICIT_ASSIGNMENT_RECOVERY",
                }
                or recovery.get("recovered_number") != current_numbers[benchmark_id]
                or recovery.get("previous_registry_state") != "USER_APPROVED_GOLD_STANDARD without gold_star_number field"
                or isinstance(recovery.get("source_pr"), bool)
                or not isinstance(recovery.get("source_pr"), int)
                or missing
            ):
                unauthorized_migrations.append(benchmark_id)
            else:
                recovered_historical_ids.add(benchmark_id)
            continue
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
        if benchmark_id not in base_numbers and benchmark_id not in recovered_historical_ids
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

    approved = [r for r in records if r.get("status") == APPROVED_STATUS]
    active = [r for r in approved if r.get("runtime_transfer") is True]
    exact_only = validate_exact_only_successors(approved, active)
    authority_records = active + exact_only

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
    for record in authority_records:
        capabilities = record.get("gold_star_capabilities") or {}
        if not bool(capabilities.get("exact_answer_authority")):
            continue
        question = normalize_exact_question(record.get("query"))
        answer = str(record.get("expected_response") or "").strip()
        if not question or not answer:
            fail(f"{record['benchmark_id']} has incomplete exact-answer authority")
        previous = exact_authority.get(question)
        if previous and previous["answer"] != answer:
            # A reviewed successor may explicitly replace only the exact-query
            # answer authority of its predecessor while leaving the predecessor
            # as the single active quality-learning contributor. Require the
            # relationship to be reciprocal; all other conflicting answers fail.
            predecessor_id = str(
                record.get("replaces_exact_query_runtime_authority_of") or ""
            ).strip()
            predecessor = next(
                (
                    item for item in authority_records
                    if item.get("benchmark_id") == predecessor_id
                ),
                None,
            )
            successor_override = bool(
                predecessor
                and previous["benchmark_id"] == predecessor_id
                and predecessor.get("runtime_exact_query_successor")
                    == record.get("benchmark_id")
                and record.get("runtime_transfer") is False
                and capabilities.get("exact_answer_authority") is True
                and capabilities.get("active_quality_contributor") is False
                and capabilities.get("deterministic_fallback_eligible") is False
            )
            if not successor_override:
                fail("conflicting exact-answer authority for normalized question: " + question)
        exact_authority[question] = {
            "benchmark_id": record["benchmark_id"],
            "answer": answer,
        }

    if len(active) + len(exact_only) != len(approved):
        fail("approved Gold Star inventory contains an unclassified runtime authority state")

    validate_numbering_metadata(registry, records)
    base_numbers, current_numbers = validate_numbering_against_base(records, registry)

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
        f"{len(approved)} approved ({len(active)} learning contributors, "
        f"{len(exact_only)} exact-query-only successors), {len(records)} total records, "
        f"{len(current_numbers)} numbered, max #{max(current_numbers.values(), default=0)}, "
        f"{len(entries)} reviews, {len(exact_authority)} exact-answer authorities; "
        "canonical-main assignment immutability PASS"
    )


if __name__ == "__main__":
    main()
