import json
from pathlib import Path


def test_qualitative_transfer_review_covers_all_active_gold_standards():
    registry=json.loads(Path("docs/qa/gold_standard_registry.json").read_text())
    active={
        r["benchmark_id"]
        for r in registry["records"]
        if r.get("subsystem")=="general-purpose-guide"
        and r.get("status")=="USER_APPROVED_GOLD_STANDARD"
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
        if (
            record.get("subsystem")!="general-purpose-guide"
            or record.get("status")!="USER_APPROVED_GOLD_STANDARD"
        ):
            continue
        assert "expected_doorway" in record, record["benchmark_id"]
        doorway=record["expected_doorway"]
        if doorway is None:
            assert record.get("doorway_status") in allowed_none, record["benchmark_id"]
        else:
            assert isinstance(doorway,dict), record["benchmark_id"]
            assert doorway.get("title","").strip(), record["benchmark_id"]
            assert doorway.get("url","").strip(), record["benchmark_id"]
