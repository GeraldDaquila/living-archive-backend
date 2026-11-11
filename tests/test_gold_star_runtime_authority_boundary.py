import json
from pathlib import Path
from general_guide_gold_standards import resolve_exact_gold_standard

def _records():
    return json.loads(Path("docs/qa/gold_standard_registry.json").read_text())["records"]

def test_current_user_approved_gold_standard_remains_runtime_eligible():
    record=next(r for r in _records() if r["status"]=="USER_APPROVED_GOLD_STANDARD" and r.get("expected_response"))
    assert resolve_exact_gold_standard(record["query"]) is not None

def test_frozen_reference_has_no_runtime_answer_authority():
    record=next(r for r in _records() if r["status"]=="FROZEN_REFERENCE_ONLY" and r.get("expected_response"))
    assert resolve_exact_gold_standard(record["query"]) is None
