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




def test_exact_question_duplicates_have_explicit_lineage_and_one_active_systems_map_exemplar():
    import json
    from pathlib import Path
    from general_guide_gold_standards import resolve_exact_gold_standard

    root = Path(__file__).resolve().parents[1]
    registry = json.loads((root / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    review = json.loads((root / "docs/qa/gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))
    records = {item["benchmark_id"]: item for item in registry["records"]}
    migrated_id = "gs-2026-11-13-04-migrated-canonical-ledger"
    live_id = "general-guide-systems-map-useful-false-confidence-gold-standard-2026-11-15"
    migrated = records[migrated_id]
    live = records[live_id]

    assert migrated["superseded_by_benchmark_id"] == live_id
    assert migrated["runtime_exact_query_successor"] == live_id
    assert migrated["runtime_transfer"] is False
    assert migrated["gold_star_capabilities"]["active_quality_contributor"] is False
    assert migrated["gold_star_capabilities"]["exact_answer_authority"] is False
    assert migrated["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert live["replaces_exact_query_runtime_authority_of"] == migrated_id
    assert live["runtime_transfer"] is True
    assert live["gold_star_capabilities"]["active_quality_contributor"] is True

    reviewed = {item["benchmark_id"] for item in review["entries"]}
    assert migrated_id not in reviewed
    assert live_id in reviewed
    resolved = resolve_exact_gold_standard(migrated["query"])
    assert resolved is not None
    assert resolved["benchmark_id"] == live_id
    assert resolved["expected_response"] == live["expected_response"]


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
            if record["benchmark_id"] in {"gs-2026-11-17-structural-change-vs-disruption", "gs-2026-11-17-consequential-action-under-uncertainty"}:
                assert doorway.get("rationale", "").strip()


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

    audit = registry["integrity_audit"]
    assert len(approved) == audit["approved_gold_star_count"]
    assert len(registry["records"]) == audit["registry_record_count"]
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
        if command[:4] == ["git", "show-ref", "--verify", "--quiet"]:
            return type("Result", (), {"stdout": "", "returncode": 0})()
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
    assert next_number != len(assignments) + 1  # Numbering follows the highest assigned ID, not the inventory size.


def test_released_gaps_85_and_86_are_allocated_only_to_their_new_approved_exemplars():
    registry = _registry()
    assignments = _numbered_approved(registry["records"])
    benchmark_85 = "general-guide-ownership-management-stewardship-comparison-gold-star-2026-11-18"
    benchmark_86 = "general-guide-archive-examples-evidence-limits-gold-star-2026-11-18"
    assert assignments[benchmark_85] == 85
    assert assignments[benchmark_86] == 86
    allocation_85 = next(item for item in registry["numbering_allocation_history"] if item["number"] == 85)
    allocation_86 = next(item for item in registry["numbering_allocation_history"] if item["number"] == 86)
    assert allocation_85["benchmark_id"] == benchmark_85
    assert allocation_86["benchmark_id"] == benchmark_86
    assert allocation_85["prior_gap_record"]["release_authorization"]["approved_by"] == "user"
    assert allocation_86["prior_gap_record"]["release_authorization"]["approved_by"] == "user"
    assert allocation_86["prior_gap_record"]["status"] == "RELEASED_FOR_FUTURE_ALLOCATION"
    assert registry["numbering_gap_register"] == []


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
        if record.get("superseded_by_benchmark_id"):
            assert record.get("runtime_transfer") is False, record["benchmark_id"]
            assert capabilities.get("exact_answer_authority") is False, record["benchmark_id"]
            assert capabilities.get("active_quality_contributor") is False, record["benchmark_id"]
            assert capabilities.get("deterministic_fallback_eligible") is False, record["benchmark_id"]
        elif record.get("runtime_transfer") is False:
            # An approved exact-query successor may own the answer without
            # becoming a second adaptive-learning contributor or fallback.
            assert capabilities.get("exact_answer_authority") is True, record["benchmark_id"]
            assert capabilities.get("active_quality_contributor") is False, record["benchmark_id"]
            assert capabilities.get("deterministic_fallback_eligible") is False, record["benchmark_id"]
            assert record.get("replaces_exact_query_runtime_authority_of"), record["benchmark_id"]
        else:
            assert record.get("runtime_transfer") is True, record["benchmark_id"]
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


def test_consequential_action_gold_star_has_bounded_structural_transfer():
    registry = _registry()
    benchmark_id = "gs-2026-11-17-consequential-action-under-uncertainty"
    record = next(r for r in registry["records"] if r["benchmark_id"] == benchmark_id)
    review = json.loads(Path("docs/qa/gold_star_qualitative_transfer_review.json").read_text())
    entry = next(r for r in review["entries"] if r["benchmark_id"] == benchmark_id)

    assert record["runtime_transfer"] is True
    assert entry["activation"] == "active_quality_contributor"
    assert entry["reasoning_family"] == "consequential_action_under_uncertainty"
    assert "what is known and unknown" in entry["transferable_discipline"]
    assert "who carries the costs" in entry["transferable_discipline"]
    assert "review signals" in entry["transferable_discipline"]
    assert "low-stakes" in entry["abstention_boundary"]
    assert "answer text" not in entry["transferable_discipline"].lower()
