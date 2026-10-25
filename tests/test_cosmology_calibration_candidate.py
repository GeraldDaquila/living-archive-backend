import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_cosmology_candidate_follows_three_paragraph_stewardship_shape_without_runtime_authority():
    registry = json.loads((ROOT / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8"))
    record = next(
        item for item in registry["records"]
        if item.get("benchmark_id") == "general-guide-living-archive-cosmology-gold-standard-2026-10-25"
    )
    assert record["status"] == "RECOVERED_HISTORICAL_RESPONSE"
    assert len(record["expected_response"].split("\n\n")) == 3
    assert record["expected_doorway"]["title"] == "The Worldview of a Conscious Human"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/2026/02/07/the-worldview-of-a-conscious-human/"
    assert "not labels for judging a person" in record["expected_response"]
    assert "not a claim that one article exhausts" in record["expected_response"]
    assert "not yet explicitly approved by the user" in record["provenance"]["approval_note"]
