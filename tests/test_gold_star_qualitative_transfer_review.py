import json
from pathlib import Path

def test_qualitative_transfer_review_covers_all_approved_gold_standards():
    registry=json.loads(Path("docs/qa/gold_standard_registry.json").read_text())
    approved={r["benchmark_id"] for r in registry["records"] if r.get("subsystem")=="general-purpose-guide" and r.get("status")=="USER_APPROVED_GOLD_STANDARD"}
    review=json.loads(Path("docs/qa/gold_star_qualitative_transfer_review.json").read_text())
    entries=review["entries"]
    assert {e["benchmark_id"] for e in entries} == approved
    assert all(e["transferable_discipline"] and e["abstention_boundary"] for e in entries)
    assert all(e["activation"]=="shadow_candidate" for e in entries)
