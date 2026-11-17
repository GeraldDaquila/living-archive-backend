import json
from pathlib import Path


def test_community_project_economic_dimensions_gold_star_preserves_exact_answer_and_doorway():
    from general_guide_composition import compose
    from general_guide_gold_standards import resolve_exact_gold_standard

    root = Path(__file__).resolve().parent
    fixture = json.loads((root / "fixtures" / "general_guide_community_project_economic_dimensions_gold_standard.json").read_text(encoding="utf-8"))
    query = fixture["query"]
    expected = fixture["expected_response"]
    registry = json.loads((root.parent / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8"))
    record = next(item for item in registry["records"] if item["benchmark_id"] == "general-guide-community-project-economic-dimensions-gold-star-2026-11-18")

    assert record["status"] == fixture["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["numbering_status"] == "UNASSIGNED"
    assert record.get("gold_star_number") is None
    assert record["rating_out_of_10"] == fixture["rating_out_of_10"] == 9.7
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["runtime_transfer"] is True
    assert record["expected_response"] == expected
    assert len(expected.split(chr(10) * 2)) == 3
    assert record["expected_doorway"] == {
        "title": fixture["expected_doorway_title"],
        "url": fixture["expected_doorway_url"],
        "rationale": fixture["expected_doorway_rationale"],
    }
    assert record["gold_star_capabilities"]["exact_answer_authority"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is True

    resolved = resolve_exact_gold_standard(query)
    assert resolved is not None
    assert resolved["benchmark_id"] == record["benchmark_id"]
    assert resolved["expected_response"] == expected
    assert resolved["doorway_title"] == fixture["expected_doorway_title"]
    assert resolved["doorway_url"] == fixture["expected_doorway_url"]
    assert resolved["doorway_rationale"] == fixture["expected_doorway_rationale"]

    provider_contract = compose(use_core=None, query=query, context_data={})
    assert provider_contract["response"] == expected
    assert provider_contract["doorway_title"] == fixture["expected_doorway_title"]
    assert provider_contract["doorway_url"] == fixture["expected_doorway_url"]

    import pytest
    pytest.importorskip("fastapi")
    import main
    deterministic_contract = main._basic_inquiry_round1_deterministic_response(
        query, {}, {}, recommendation_available=False
    )
    assert deterministic_contract["response"] == expected
    assert deterministic_contract["doorway_title"] == fixture["expected_doorway_title"]
    assert deterministic_contract["recommendation"]["url"] == fixture["expected_doorway_url"]

    assert resolve_exact_gold_standard("How should a Guide steward a community project?") is None


def test_community_project_economic_dimensions_gold_star_has_active_transfer_review():
    root = Path(__file__).resolve().parent
    review = json.loads((root.parent / "docs" / "qa" / "gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))
    entry = next(item for item in review["entries"] if item["benchmark_id"] == "general-guide-community-project-economic-dimensions-gold-star-2026-11-18")
    assert entry["activation"] == "active_quality_contributor"
    assert entry["reasoning_family"] == "community_project_economic_accounting_and_shared_resource_stewardship"
    assert "distributional and lifecycle-aware" in entry["transferable_discipline"]
    assert "Do not infer project-specific outcomes" in entry["abstention_boundary"]
