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
        "NOT_EVALUATED",
        "NOT_EVALUATED",
    }
    for record in registry["records"]:
        if record.get("status")!="USER_APPROVED_GOLD_STANDARD":
            continue
        assert "expected_doorway" in record, record["benchmark_id"]
        doorway=record["expected_doorway"]
        if doorway is None:
            assert record.get("doorway_status") in allowed_none, record["benchmark_id"]
            if record.get("doorway_status") == "NOT_EVALUATED":
                capabilities = record.get("gold_star_capabilities") or {}
                boundary = capabilities.get("abstention_boundary", "")
                assert capabilities.get("exact_answer_authority") is False, record["benchmark_id"]
                assert capabilities.get("deterministic_fallback_eligible") is False, record["benchmark_id"]
                assert "NOT_EVALUATED" in boundary, record["benchmark_id"]
                assert "Do not infer" in boundary, record["benchmark_id"]
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
    # registry directly against canonical main, not a stale branch count.
    from scripts import validate_gold_star_registry as validator

    base_records = _registry()["records"]
    stale_records = [
        record for record in base_records
        if record.get("benchmark_id")
        != "general-guide-reflection-vs-therapy-boundary-gold-standard-2026-11-16"
    ]

    def fake_run(command, **kwargs):
        if command[:3] == ["git", "remote", "get-url"]:
            return type("Result", (), {"stdout": "https://github.com/GeraldDaquila/living-archive-backend.git", "returncode": 0})()
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
        elif record.get("runtime_transfer") is False and capabilities.get("generation_class") == "user_approved_response_quality_exemplar":
            # Frozen response-quality exemplars are approved evaluation references,
            # not runtime answer authority or adaptive contributors.
            assert capabilities.get("exact_answer_authority") is False, record["benchmark_id"]
            assert capabilities.get("active_quality_contributor") is False, record["benchmark_id"]
            assert capabilities.get("deterministic_fallback_eligible") is False, record["benchmark_id"]
            assert record.get("paired_active_benchmark_id"), record["benchmark_id"]
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
            assert (
                record.get("reasoning_family", "")
                or capabilities.get("reasoning_family", "")
            ).strip(), record["benchmark_id"]
            # Immutable approved records may carry transfer discipline inside
            # gold_star_capabilities rather than duplicate mutable top-level fields.
            transferable_lesson = (
                record.get("transferable_lesson", "")
                or capabilities.get("transferable_discipline", "")
            )
            transfer_boundary = (
                record.get("transfer_boundary", "")
                or capabilities.get("abstention_boundary", "")
            )
            assert transferable_lesson.strip(), record["benchmark_id"]
            assert transfer_boundary.strip(), record["benchmark_id"]
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


def test_reflexive_institutional_critique_gold_star_is_registered_and_bounded():
    from pathlib import Path
    import json

    root = Path(__file__).resolve().parents[1]
    registry = json.loads((root / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    review = json.loads((root / "docs/qa/gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))
    benchmark_id = "gs-2026-11-20-reflexive-institutional-critique"
    record = next(item for item in registry["records"] if item["benchmark_id"] == benchmark_id)
    entry = next(item for item in review["entries"] if item["benchmark_id"] == benchmark_id)

    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["rating_out_of_10"] == 9.6
    assert record["explicit_user_elevation_approval"] is True
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["doorway_status"] == "INTENTIONALLY_NONE_APPROVED"
    assert record["expected_doorway"] is None
    assert "independent method of scrutinizing" in record["doorway_omission_exception_reason"]
    assert len(record["expected_response"].split("\n\n")) == 6
    for phrase in (
        "independent corroboration",
        "internal coherence and external adequacy",
        "revision conditions",
        "not independently establish that what it says is true",
    ):
        assert phrase in record["expected_response"]
    assert entry["activation"] == "active_quality_contributor"
    assert entry["reasoning_family"] == record["reasoning_family"]
    assert entry["transferable_discipline"] == record["transferable_lesson"]
    assert entry["abstention_boundary"] == record["transfer_boundary"]
    assert len(review["entries"]) == sum(
        item.get("status") == "USER_APPROVED_GOLD_STANDARD" and item.get("runtime_transfer") is True
        for item in registry["records"]
    )


def test_power_responsibility_gold_star_preserves_live_answer_doorway_and_bounded_transfer():
    root = Path(__file__).resolve().parents[1]
    registry = json.loads((root / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    review = json.loads((root / "docs/qa/gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))
    transfer_map = json.loads((root / "docs/qa/gold_star_transferability_map.json").read_text(encoding="utf-8"))
    benchmark_id = "gs-2026-11-20-power-responsibility-proportional-accountability"
    record = next(item for item in registry["records"] if item["benchmark_id"] == benchmark_id)
    entry = next(item for item in review["entries"] if item["benchmark_id"] == benchmark_id)
    mapped = next(item for item in transfer_map["entries"] if item["benchmark_id"] == benchmark_id)

    expected = "Power and responsibility are connected because the ability to influence what happens creates a corresponding need to account for how that influence is used and what effects it has. Power is not limited to holding a formal position or issuing decisions: it can also operate through control of information, access, resources, attention, relationships, or the choices available to other people. Responsibility concerns how a person or institution answers for the use of that influence and for consequences within its meaningful sphere of control.\n\nThe relationship is proportional, but not a simple equation. The more influence someone has over an outcome, the stronger the reason to explain decisions, consider who may be affected, respect other people's agency, and correct preventable harm. Formal authority can make these duties visible, but quiet or informal influence can carry responsibility too. At the same time, responsibility should not be assigned as though someone controlled conditions they could not reasonably change. A fair account distinguishes a person's actual influence, knowledge, role, and capacity from outcomes imposed by wider constraints.\n\nThis connection also works in the other direction: responsibility gives power its proper limits and purpose. Without accountability, influence can become arbitrary or self-serving; without enough agency or authority to act, responsibility can become an unfair burden rather than a meaningful obligation. The practical test is to ask: who can shape this decision or condition, who will experience its effects, what can the influential person reasonably do, and how can those affected question, correct, or seek an explanation? The aim is not to eliminate power, but to make its exercise answerable and proportionate to its reach."
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "What is the relationship between power and responsibility?"
    assert record["expected_response"] == expected
    assert len(expected.split("\n\n")) == 3
    assert record["rating_out_of_10"] == 9.6
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is True
    from general_guide_gold_standards import resolve_exact_gold_standard
    resolved = resolve_exact_gold_standard(record["query"])
    assert resolved is not None
    assert resolved["benchmark_id"] == benchmark_id
    assert resolved["expected_response"] == expected
    assert resolved["doorway_title"] == "Leadership Foundations"
    assert resolved["doorway_url"] == "https://geralddaquila.com/leadership-foundations/"
    assert resolve_exact_gold_standard("What is the relationship between power and accountability?") is None
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert record["expected_doorway"] == {
        "title": "Leadership Foundations",
        "url": "https://geralddaquila.com/leadership-foundations/",
        "rationale": "The live Continue Exploring card identifies leadership as a human systems function through self-governance, relationships, responsibility, governance, pressure, and decision making.",
    }
    assert record["doorway_status"] == "VERIFIED_CANONICAL_DESTINATION"
    assert record["numbering_status"] == "UNASSIGNED"
    assert entry["activation"] == "active_quality_contributor"
    assert entry["reasoning_family"] == record["reasoning_family"]
    assert entry["transferable_discipline"] == record["transferable_lesson"]
    assert entry["abstention_boundary"] == record["transfer_boundary"]
    assert mapped["family"] == record["reasoning_family"]
    assert mapped["structural_lesson"] == record["transferable_lesson"]
    assert len(review["entries"]) == registry["integrity_audit"]["active_quality_contributor_count"] == 133
    assert len(transfer_map["entries"]) == transfer_map["coverage"]["map_entries"] == 129


def test_systemic_explanation_accessibility_gold_star_is_exactly_approved_and_bounded():
    from general_guide_gold_standards import resolve_exact_gold_standard

    root = Path(__file__).resolve().parents[1]
    registry = json.loads((root / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    review = json.loads((root / "docs/qa/gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))
    transfer_map = json.loads((root / "docs/qa/gold_star_transferability_map.json").read_text(encoding="utf-8"))
    benchmark_id = "gs-2026-11-20-systemic-explanation-accessibility"
    record = next(item for item in registry["records"] if item["benchmark_id"] == benchmark_id)
    entry = next(item for item in review["entries"] if item["benchmark_id"] == benchmark_id)
    mapped = next(item for item in transfer_map["entries"] if item["benchmark_id"] == benchmark_id)

    expected = "The Guide should make the explanation simple without making the issue simplistic. Begin with the clearest short answer: a systemic issue persists because several conditions and relationships reinforce one another, not necessarily because of one person's mistake.\n\nThen name the main mechanism in ordinary language. Briefly show which rules, incentives, resources, relationships, or feedback patterns help reproduce the problem. Use only the connections that materially explain it; distinguish what is known from what is inferred, and do not pretend that one cause explains everything.\n\nFinish with why the pattern matters and, where useful, one practical point of leverage or next step. Offer deeper layers only if the user wants them. In short: simplify the explanation, not the system."
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "How should The Guide explain a systemic issue to a user seeking a simple answer?"
    assert record["expected_response"] == expected
    assert record["rating_out_of_10"] == 9.8
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    resolved = resolve_exact_gold_standard(record["query"])
    assert resolved is not None
    assert resolved["benchmark_id"] == benchmark_id
    assert resolved["expected_response"] == expected
    assert resolve_exact_gold_standard("How should The Guide explain a systemic issue to users seeking a simple answer?") is None
    assert entry["activation"] == "active_quality_contributor"
    assert entry["reasoning_family"] == record["reasoning_family"]
    assert entry["transferable_discipline"] == record["transferable_lesson"]
    assert entry["abstention_boundary"] == record["transfer_boundary"]
    assert mapped["family"] == record["reasoning_family"]
    assert mapped["structural_lesson"] == record["transferable_lesson"]
    assert len(review["entries"]) == registry["integrity_audit"]["active_quality_contributor_count"] == 133
    assert len(transfer_map["entries"]) == transfer_map["coverage"]["map_entries"] == 129


def test_community_freedom_shared_responsibility_is_mapped_with_its_boundary():
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    transfer_map = json.loads((root / "docs/qa/gold_star_transferability_map.json").read_text(encoding="utf-8"))
    entry = next(item for item in transfer_map["entries"] if item["benchmark_id"] == "gs-2026-11-22-community-freedom-shared-responsibility-decision")
    assert entry["family"] == "community_freedom_shared_responsibility_proportionate_decision"
    assert "meaningful agency" in entry["structural_lesson"]
    assert "automatic authority to override individual rights" in entry["structural_lesson"]
    assert "jurisdiction-specific legal analysis" in entry["abstention_boundary"]
