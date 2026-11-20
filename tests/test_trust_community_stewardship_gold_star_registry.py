import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "qa" / "gold_standard_registry.json"
FIXTURE = ROOT / "tests" / "fixtures" / "general_guide_trust_community_stewardship_candidate.json"
TRANSFER_REVIEW = ROOT / "docs" / "qa" / "gold_star_qualitative_transfer_review.json"


def test_trust_community_stewardship_is_user_approved_bounded_gold_star():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    transfer = json.loads(TRANSFER_REVIEW.read_text(encoding="utf-8"))
    transfer_map = json.loads((ROOT / "docs" / "qa" / "gold_star_transferability_map.json").read_text(encoding="utf-8"))
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-trust-community-stewardship-2026-10-24"
    )

    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert fixture["status"] == record["status"]
    assert record["query"] == fixture["query"] == "What is the role of trust in community stewardship?"
    assert record["expected_response"] == fixture["expected_response"]
    assert record["expected_doorway"] == fixture["expected_doorway"]
    assert record["doorway_status"] == "VERIFIED_CANONICAL_DESTINATION"
    assert record["expected_doorway"]["title"] == "Trust Architecture"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/trust-architecture/"

    capabilities = record["gold_star_capabilities"]
    assert record["runtime_transfer"] is True
    assert capabilities["active_quality_contributor"] is True
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["deterministic_fallback_eligible"] is False
    assert record["numbering_status"] == "UNASSIGNED"
    assert "rating_out_of_10" not in record

    review_entry = next(
        item for item in transfer["entries"]
        if item["benchmark_id"] == record["benchmark_id"]
    )
    assert review_entry["activation"] == "active_quality_contributor"
    assert review_entry["transferable_discipline"] == record["transferable_lesson"]
    assert review_entry["abstention_boundary"] == record["transfer_boundary"]
    mapped = next(item for item in transfer_map["entries"] if item["benchmark_id"] == record["benchmark_id"])
    assert mapped["family"] == record["reasoning_family"]
    assert mapped["structural_lesson"] == record["transferable_lesson"]
    assert transfer_map["coverage"]["map_entries"] == len(transfer_map["entries"]) == 123


def test_trust_gold_star_approval_does_not_change_exact_answer_authority():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-trust-community-stewardship-2026-10-24"
    )
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert record["transfer_boundary"]
