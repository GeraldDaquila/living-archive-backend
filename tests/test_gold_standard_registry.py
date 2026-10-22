import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "docs" / "qa" / "gold_standard_registry.json"
STEWARDSHIP_FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "general_guide_stewardship_gold_standard.json"
)


def _registry():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_registry_has_unique_ids_and_required_provenance():
    registry = _registry()
    assert registry["registry_id"] == "living-archive-gold-standard-registry"
    assert registry["schema_version"] == "1.0.0"
    records = registry["records"]
    ids = [record["benchmark_id"] for record in records]
    assert len(ids) == len(set(ids))
    assert records

    for record in records:
        assert record["query"].strip()
        assert record["expected_response"].strip()
        assert record["subsystem"] == "general-purpose-guide"
        assert record["status"] in {
            "FROZEN_REFERENCE_ONLY",
            "RECOVERED_HISTORICAL_RESPONSE",
            "CONFIRMED_CASE",
            "NEEDS_SOURCE_RECOVERY",
            "CANDIDATE",
        }
        assert record["provenance"]["source_path"]
        assert record["assertions"]
        assert record["freeze_policy"]


def test_frozen_stewardship_record_matches_authoritative_fixture_exactly():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-stewardship-gold-standard-2026-10-14"
    )
    fixture = json.loads(STEWARDSHIP_FIXTURE_PATH.read_text(encoding="utf-8"))

    assert record["status"] == fixture["status"]
    assert record["query"] == fixture["query"]
    assert record["expected_response"] == fixture["expected_response"]
    assert record["expected_doorway"]["title"] == fixture["expected_doorway_title"]
    assert len(record["expected_response"].split("\\n\\n")) == 3


def test_recovered_compound_stewardship_record_preserves_evidence_boundary():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-stewardship-compound-2026-10"
    )
    assert record["status"] == "RECOVERED_HISTORICAL_RESPONSE"
    assert record["query"] == "What is stewardship and why does it matter now more than ever?"
    assert len(record["expected_response"]) == 861
    assert len(record["expected_response"].split("\\n\\n")) == 3
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/level-1-case-catalog/"
    assert "do not independently prove the exact live response text" in record["provenance"]["evidence_boundary"]


def test_reciprocity_record_is_explicit_about_unmerged_source():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-reciprocity-gold-standard-2026-10-19"
    )
    assert record["status"] == "FROZEN_REFERENCE_ONLY"
    assert len(record["expected_response"].split("\\n\\n")) == 3
    assert "open, unmerged historical PR branch" in record["provenance"]["caveat"]
