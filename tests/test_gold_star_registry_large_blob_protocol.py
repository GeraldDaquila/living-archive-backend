import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "qa" / "gold_standard_registry.json"
FIXTURE = ROOT / "tests" / "fixtures" / "general-guide-nonprofit-mission-care-operational-capacity-2026-11-28.json"
RUNBOOK = ROOT / "docs" / "qa" / "GOLD_STAR_REGISTRY_LARGE_FILE_OPERATIONS.md"
BENCHMARK_ID = "general-guide-nonprofit-mission-care-operational-capacity-2026-11-28"


def test_canonical_registry_and_fixture_reconcile_for_nonprofit_gold_star():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    records = registry["records"]
    ids = [record["benchmark_id"] for record in records]
    approved = [record for record in records if record.get("status") == "USER_APPROVED_GOLD_STANDARD"]
    active = [record for record in approved if record.get("runtime_transfer") is True]
    response_quality = [
        record for record in approved
        if record.get("gold_star_capabilities", {}).get("generation_class")
        == "user_approved_response_quality_exemplar"
    ]
    standalone = [
        record for record in approved
        if record.get("gold_star_capabilities", {}).get("standalone_response_quality_exemplar") is True
    ]
    numbered = [record for record in approved if isinstance(record.get("gold_star_number"), int)]
    unassigned = [record for record in approved if record.get("numbering_status") == "UNASSIGNED"]
    audit = registry["integrity_audit"]
    assert registry["audit"] == audit, "Canonical audit mirrors must remain synchronized."

    assert len(ids) == len(set(ids)), "Canonical benchmark IDs must be unique."
    assert len(records) == audit["registry_record_count"]
    assert len(approved) == audit["approved_gold_star_count"]
    assert len(active) == audit["active_quality_contributor_count"]
    assert len(response_quality) == audit["approved_response_quality_exemplar_count"]
    assert len(numbered) == audit["numbered_gold_star_record_count"]
    assert len(unassigned) == audit["unassigned_approved_gold_star_count"]
    assert len(standalone) == 21

    record = next(record for record in approved if record["benchmark_id"] == BENCHMARK_ID)
    assert record["expected_response"] == fixture["expected_response"]
    assert record["query"] == fixture["query"]
    assert record["runtime_transfer"] is False
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert record["gold_star_capabilities"]["active_quality_contributor"] is False
    assert record["gold_star_capabilities"]["standalone_response_quality_exemplar"] is True
    assert record["doorway_status"] == "NOT_EVALUATED"
    assert record["expected_doorway"] is None

    doorway_fixture = json.loads(
        (ROOT / "tests/fixtures/general-guide-nonprofit-mission-care-operational-capacity-doorway-2026-11-28.json").read_text(encoding="utf-8")
    )
    doorway_record = next(item for item in approved if item["benchmark_id"] == doorway_fixture["benchmark_id"])
    assert doorway_record["expected_response"] == doorway_fixture["expected_response"]
    assert doorway_record["expected_doorway"] == doorway_fixture["expected_doorway"]
    assert doorway_record["doorway_status"] == "NOT_EVALUATED"
    assert doorway_record["expected_doorway"] is None
    assert doorway_record["runtime_transfer"] is False
    assert doorway_record["numbering_status"] == "UNASSIGNED"


def test_large_registry_git_database_runbook_is_present_and_complete():
    guide = RUNBOOK.read_text(encoding="utf-8")
    for required in (
        "fetch_blob",
        "create_blob",
        "create_tree",
        "create_commit",
        "update_ref",
        "expected_sha",
        "force=false",
        "sole authoritative",
        "Never split the authoritative registry",
        "Never use a stale blob SHA or branch head",
    ):
        assert required in guide
