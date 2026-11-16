import json

import pytest

import general_guide_gold_standards as standards

SPIRITUAL_BYPASSING = "What is spiritual bypassing, and why does it matter?"

def test_intentionally_none_approved_record_forbids_runtime_doorway():
    record = standards.resolve_exact_gold_standard(SPIRITUAL_BYPASSING)
    assert record is not None
    assert record["forbids_doorway"] is True
    assert record["doorway_title"] == ""
    assert record["doorway_url"] == ""

def test_intentionally_none_metadata_cannot_conflict_with_expected_doorway(tmp_path, monkeypatch):
    registry = {"records": [{"benchmark_id":"contradictory-doorway-fixture","status":"USER_APPROVED_GOLD_STANDARD","query":"Fixture question?","expected_response":"Fixture answer.","doorway_status":"INTENTIONALLY_NONE_APPROVED","expected_doorway":{"title":"Contradictory doorway","url":"https://geralddaquila.com/contradiction/"}}]}
    path = tmp_path / "gold_standard_registry.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    monkeypatch.setattr(standards, "_REGISTRY_PATH", path)
    with pytest.raises(ValueError, match="intentionally-none"):
        standards.load_approved_standards()
