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
    assert len(assignments) == 27
    assert max(numbers) == 88
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
    # Exercise the production comparison against the actual main registry.
    # No subprocess patching: load the real base from Git and simulate a stale
    # proposed registry that has dropped the #88 holder.
    from scripts import validate_gold_star_registry as validator

    main_text = subprocess.run(
        ["git", "show", "origin/main:docs/qa/gold_standard_registry.json"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    base_records = json.loads(main_text)["records"]
    stale_records = [
        record for record in base_records
        if record.get("benchmark_id")
        != "general-guide-reflection-vs-therapy-boundary-gold-standard-2026-11-16"
    ]
    with pytest.raises(SystemExit, match="removed/demoted"):
        validator.validate_numbering_against_base(stale_records)


def test_next_number_is_based_on_registry_maximum_not_approved_count():
    registry = _registry()
    assignments = _numbered_approved(registry["records"])
    next_number = max(assignments.values()) + 1
    assert next_number == 89
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
