import json
import pytest
from pathlib import Path


def test_qualitative_transfer_review_covers_all_active_gold_standards():
    registry=json.loads(Path("docs/qa/gold_standard_registry.json").read_text())
    active={
        r["benchmark_id"]
        for r in registry["records"]
        if r.get("status")=="USER_APPROVED_GOLD_STANDARD"
        and r.get("runtime_transfer") is True
    }
    review=json.loads(Path("docs/qa/gold_star_qualitative_transfer_review.json").read_text())
    entries=review["entries"]
    reviewed={e["benchmark_id"] for e in entries}
    assert reviewed == active
    assert len(entries) == len(reviewed)
    assert all(e["transferable_discipline"] and e["abstention_boundary"] for e in entries)
    assert all(e["activation"]=="active_quality_contributor" for e in entries)


def test_every_approved_gold_star_has_a_complete_or_explicitly_withheld_doorway():
    registry=json.loads(Path("docs/qa/gold_standard_registry.json").read_text())
    allowed_none={
        "INTENTIONALLY_NONE_APPROVED",
        "LEGACY_INCOMPLETE_NOT_APPROVED",
        "NOT_APPROVED_CONCEPTUAL_MISMATCH",
    }
    for record in registry["records"]:
        if record.get("status")!="USER_APPROVED_GOLD_STANDARD":
            continue
        assert "expected_doorway" in record, record["benchmark_id"]
        doorway=record["expected_doorway"]
        if doorway is None:
            assert record.get("doorway_status") in allowed_none, record["benchmark_id"]
        else:
            assert isinstance(doorway,dict), record["benchmark_id"]
            assert doorway.get("title","").strip(), record["benchmark_id"]
            assert doorway.get("url","").strip(), record["benchmark_id"]


import json
import subprocess
from pathlib import Path


def _registry():
    return json.loads(Path("docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))


def _numbered_approved(records):
    return {
        record["benchmark_id"]: record["gold_star_number"]
        for record in records
        if record.get("status") == "USER_APPROVED_GOLD_STANDARD"
        and record.get("gold_star_number") is not None
    }


def test_canonical_gold_star_numbering_matches_current_inventory():
    registry = _registry()
    approved = [
        record for record in registry["records"]
        if record.get("status") == "USER_APPROVED_GOLD_STANDARD"
    ]
    assignments = _numbered_approved(registry["records"])
    numbers = list(assignments.values())

    assert len(approved) == 80
    assert len(registry["records"]) == 117
    assert len(assignments) == registry["integrity_audit"]["numbered_gold_star_record_count"]
    assert max(numbers) == registry["integrity_audit"]["highest_assigned_gold_star_number"]
    assert len(numbers) == len(set(numbers))
    assert assignments[
        "general-guide-formal-actual-power-structure-gold-standard-2026-11-16"
    ] == 87
    assert assignments[
        "general-guide-reflection-vs-therapy-boundary-gold-standard-2026-11-16"
    ] == 88


def test_canonical_audit_metadata_is_derived_not_independent():
    registry = _registry()
    approved = [
        record for record in registry["records"]
        if record.get("status") == "USER_APPROVED_GOLD_STANDARD"
    ]
    assignments = _numbered_approved(registry["records"])
    audit = registry["integrity_audit"]

    assert audit["approved_gold_star_count"] == len(approved)
    assert audit["registry_record_count"] == len(registry["records"])
    assert audit["numbered_gold_star_record_count"] == len(assignments)
    assert audit["highest_assigned_gold_star_number"] == max(assignments.values())


def test_numbering_guard_rejects_stale_branch_that_drops_latest_gold_star(monkeypatch):
    # Exercise the same invariant the CI validator uses: compare the proposed
    # registry against the exact merge-base registry, not a stale branch count.
    from scripts import validate_gold_star_registry as validator

    base_records = _registry()["records"]
    stale_records = [
        record for record in base_records
        if record.get("benchmark_id")
        != "general-guide-reflection-vs-therapy-boundary-gold-standard-2026-11-16"
    ]

    def fake_run(command, **kwargs):
        if command[:3] == ["git", "merge-base", "HEAD"]:
            return type("Result", (), {"stdout": "fake-base", "returncode": 0})()
        if command[:2] == ["git", "show"]:
            return type(
                "Result", (), {
                    "stdout": json.dumps({"records": base_records}),
                    "returncode": 0,
                }
            )()
        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(validator.subprocess, "run", fake_run)
    with pytest.raises(SystemExit, match="removed/demoted"):
        validator.validate_numbering_against_base(stale_records)


def test_next_number_is_based_on_registry_maximum_not_approved_count():
    registry = _registry()
    assignments = _numbered_approved(registry["records"])
    next_number = max(assignments.values()) + 1
    assert next_number == registry["integrity_audit"]["highest_assigned_gold_star_number"] + 1
    assert len(assignments) != max(assignments.values())  # 27 numbered, max number 88


def test_gaps_85_and_86_are_not_backfilled():
    registry = _registry()
    assignments = _numbered_approved(registry["records"])
    assert 85 not in assignments.values()
    assert 86 not in assignments.values()


def test_qualitative_transfer_reviews_remain_aligned():
    registry = _registry()
    reviews = json.loads(
        Path("docs/qa/gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8")
    )
    active = {
        r["benchmark_id"]
        for r in registry["records"]
        if r.get("status") == "USER_APPROVED_GOLD_STANDARD"
        and r.get("runtime_transfer") is True
    }
    reviewed = {r["benchmark_id"] for r in reviews["entries"]}
    assert active == reviewed
    assert len(reviews["entries"]) == len(reviewed)


def test_approved_gold_stars_have_complete_provenance_and_quality_contract():
    registry = _registry()
    approved = [
        record for record in registry["records"]
        if record.get("status") == "USER_APPROVED_GOLD_STANDARD"
    ]
    for record in approved:
        assert record.get("query", "").strip(), record["benchmark_id"]
        assert record.get("expected_response", "").strip(), record["benchmark_id"]
        assert record.get("known_theme", "").strip(), record["benchmark_id"]
        freeze_policy = record.get("freeze_policy")
        if record.get("legacy_approval_grandfathered") is True:
            if isinstance(freeze_policy, dict):
                assert freeze_policy.get("status") in {"FROZEN_AFTER_APPROVAL", "FROZEN_REFERENCE_ONLY"}, record["benchmark_id"]
                assert freeze_policy.get("change_requires"), record["benchmark_id"]
            else:
                assert isinstance(freeze_policy, str) and freeze_policy.strip(), record["benchmark_id"]
        else:
            assert freeze_policy in {
                "immutable_user_approved_gold_standard",
                "Preserve approved expected_response. Change only with explicit user authorization and a separately documented benchmark-version change.",
                "Preserve exact accepted response verbatim. Create a dedicated fixture and test separately from the existing October 14 stewardship fixture; do not change use_core.py or claim the deterministic production path generated this answer.",
            }, record["benchmark_id"]
        capabilities = record.get("gold_star_capabilities")
        assert isinstance(capabilities, dict), record["benchmark_id"]
        assert capabilities.get("active_quality_contributor") is True, record["benchmark_id"]
        assert record.get("assertions"), record["benchmark_id"]

        legacy = record.get("legacy_approval_grandfathered") is True
        provenance = record.get("provenance")
        assert isinstance(provenance, dict), record["benchmark_id"]
        if legacy:
            assert record.get("legacy_approval_grandfathered_reason", "").strip(), record["benchmark_id"]
            assert (
                provenance.get("source", "").strip()
                or provenance.get("evidence", "").strip()
                or record.get("legacy_approval_grandfathered_reason", "").strip()
            ), record["benchmark_id"]
        else:
            assert isinstance(record.get("rating_out_of_10", record.get("rating")), (int, float)), record["benchmark_id"]
            assert record.get("user_reviewed_response") is True, record["benchmark_id"]
            assert record.get("explicit_user_elevation_approval") is True, record["benchmark_id"]
            assert record.get("elevation_approval_evidence", "").strip(), record["benchmark_id"]
            assert record.get("approval_state", "").strip(), record["benchmark_id"]
            assert record.get("user_approved_at", "").strip(), record["benchmark_id"]
            assert record.get("reasoning_family", "").strip(), record["benchmark_id"]
            assert record.get("transferable_lesson", "").strip(), record["benchmark_id"]
            assert record.get("transfer_boundary", "").strip(), record["benchmark_id"]
            assert provenance.get("source", "").strip(), record["benchmark_id"]
            assert (
                provenance.get("source_date", "").strip()
                or provenance.get("approved_at", "").strip()
            ), record["benchmark_id"]
