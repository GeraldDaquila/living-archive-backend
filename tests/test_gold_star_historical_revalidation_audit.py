import json
from pathlib import Path


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_historical_revalidation_audit_is_a_valid_scoped_registry_subset():
    registry = _read("docs/qa/gold_standard_registry.json")
    audit = _read("docs/qa/gold_star_historical_revalidation_audit.json")
    registry_by_id = {record["benchmark_id"]: record for record in registry["records"]}
    audit_ids = [record["benchmark_id"] for record in audit["records"]]

    assert len(audit_ids) == len(set(audit_ids))
    assert set(audit_ids) <= set(registry_by_id)
    assert all(record["audit_lane"] for record in audit["records"])
    assert audit["scope"]["audit_population"] == "selected_historical_tranche"
    assert audit["scope"]["historical_audit_records"] == len(audit["records"])
    assert audit["scope"]["canonical_registry_records"] == len(registry["records"])

    for record in audit["records"]:
        canonical = registry_by_id[record["benchmark_id"]]
        assert record["current_status"] == canonical["status"]

    assert audit["summary"]["approved_gold_standards_in_audited_subset"] == sum(
        record["status"] == "USER_APPROVED_GOLD_STANDARD"
        for record in (registry_by_id[item["benchmark_id"]] for item in audit["records"])
    )
    assert audit["summary"]["superseded_gold_standards_in_audited_subset"] == sum(
        record["status"] == "SUPERSEDED_GOLD_STANDARD"
        for record in (registry_by_id[item["benchmark_id"]] for item in audit["records"])
    )
    assert audit["summary"]["current_gold_standard"] == audit["summary"][
        "approved_gold_standards_in_audited_subset"
    ]


def test_historical_batch_audit_distinguishes_snapshot_from_current_registry():
    registry = _read("docs/qa/gold_standard_registry.json")
    batch = _read("docs/qa/gold_star_registry_batch_audit.json")
    transfer_map = _read("docs/qa/gold_star_transferability_map.json")
    approved = [
        record for record in registry["records"]
        if record.get("status") == "USER_APPROVED_GOLD_STANDARD"
    ]
    runtime_transfer = [
        record for record in approved if record.get("runtime_transfer") is True
    ]

    assert batch["scope"]["classification_population"] == "historical_approved_tranche"
    assert batch["totals"]["canonical_registry_records"] == len(registry["records"])
    assert batch["totals"]["canonical_approved_gold_standards"] == len(approved)
    assert batch["totals"]["canonical_runtime_transfer_approved"] == len(runtime_transfer)
    general_purpose_runtime_transfer = [
        record for record in approved
        if record.get("subsystem") == "general-purpose-guide"
        and record.get("runtime_transfer") is True
    ]
    assert batch["totals"]["general_purpose_runtime_transfer_records"] == len(
        general_purpose_runtime_transfer
    )
    assert batch["totals"]["general_purpose_transfer_map_entries"] == len(
        transfer_map["entries"]
    )
    assert batch["totals"]["historical_batch_classifications"] == len(
        batch["classifications"]
    )
    ids = [record["benchmark_id"] for record in batch["classifications"]]
    assert len(ids) == len(set(ids))
    assert set(ids) <= {record["benchmark_id"] for record in registry["records"]}
