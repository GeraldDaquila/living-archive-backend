import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_cosmology_gold_standard_retains_exact_answer_authority_and_scope():
    registry = json.loads((ROOT / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8"))
    record = next(
        item for item in registry["records"]
        if item.get("benchmark_id") == "general-guide-living-archive-cosmology-gold-standard-2026-10-25"
    )
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["gold_star_capabilities"]["exact_answer_authority"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert len(record["expected_response"].split("\n\n")) == 3
    assert record["expected_doorway"]["title"] == "The Worldview of a Conscious Human"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/2026/02/07/the-worldview-of-a-conscious-human/"
    assert "not labels for judging a person" in record["expected_response"]
    assert "not a claim that one article exhausts" in record["expected_response"]
    assert "User explicitly approved promotion to gold standard" in record["provenance"]["user_approval"]
