import json
from pathlib import Path


def test_transferability_map_covers_all_runtime_transfer_eligible_general_guide_gold_standards():
    registry = json.loads(Path("docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    eligible = {
        record["benchmark_id"]
        for record in registry["records"]
        if record.get("subsystem") == "general-purpose-guide"
        and record.get("status") == "USER_APPROVED_GOLD_STANDARD"
        and record.get("runtime_transfer") is True
    }
    mapped = json.loads(Path("docs/qa/gold_star_transferability_map.json").read_text(encoding="utf-8"))
    entries = mapped["entries"]
    ids = [entry["benchmark_id"] for entry in entries]

    assert len(ids) == len(set(ids))
    assert eligible == set(ids)
    assert "general_purpose_runtime_transfer_records" not in mapped["coverage"]
    assert "map_entries" not in mapped["coverage"]
    assert all(
        entry["role"] in {"cross_question_candidate", "review_before_transfer", "exact_benchmark"}
        for entry in entries
    )
    assert all(entry.get("abstention_boundary", "").strip() for entry in entries)
