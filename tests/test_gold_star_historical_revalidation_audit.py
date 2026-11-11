import json
from pathlib import Path

def test_historical_revalidation_audit_covers_entire_registry():
    registry=json.loads(Path("docs/qa/gold_standard_registry.json").read_text())
    audit=json.loads(Path("docs/qa/gold_star_historical_revalidation_audit.json").read_text())
    registry_ids={r["benchmark_id"] for r in registry["records"]}
    audit_ids={r["benchmark_id"] for r in audit["records"]}
    assert registry_ids == audit_ids
    assert all(r["audit_lane"] for r in audit["records"])
