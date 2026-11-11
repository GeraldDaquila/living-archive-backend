import json
from pathlib import Path

def test_transferability_map_covers_all_approved_gold_standards():
    registry=json.loads(Path("docs/qa/gold_standard_registry.json").read_text())
    approved={r["benchmark_id"] for r in registry["records"] if r.get("subsystem")=="general-purpose-guide" and r.get("status")=="USER_APPROVED_GOLD_STANDARD"}
    mapped=json.loads(Path("docs/qa/gold_star_transferability_map.json").read_text())
    ids={e["benchmark_id"] for e in mapped["entries"]}
    assert approved == ids
    assert all(e["role"] in {"cross_question_candidate","review_before_transfer","exact_benchmark"} for e in mapped["entries"])
