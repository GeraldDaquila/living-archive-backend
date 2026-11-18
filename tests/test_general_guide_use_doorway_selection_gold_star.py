"""Gold Star contract for question-specific USE doorway warrant and selection."""

import json
from pathlib import Path

import main

QUERY = "A response contains an accurate explanation but offers no relevant Archive doorway. How should USE determine whether a doorway is warranted and select the appropriate next destination?"


def test_use_doorway_question_selects_verified_knowledge_and_sensemaking_navigator():
    family = main._select_verified_doorway_conceptual_family(QUERY)
    assert family == "use_doorway_selection"
    doorway = main._VERIFIED_CONCEPTUAL_FAMILY_DOORWAYS[family]
    assert doorway["title"] == "The Living Archive Navigator: Volume III – Knowledge & Sensemaking"
    assert doorway["url"] == "https://geralddaquila.com/the-living-archive-navigator-volume-iii/"
    assert "Reference Maps" in doorway["rationale"]
    assert "sensemaking" in doorway["rationale"]


def test_use_doorway_question_restores_topic_specific_doorway_not_compass():
    result = main._guide_restore_verified_doorway({"response": "A complete answer."}, QUERY)
    assert result["recommendation"]["title"] == "The Living Archive Navigator: Volume III – Knowledge & Sensemaking"
    assert result["recommendation"]["url"] == "https://geralddaquila.com/the-living-archive-navigator-volume-iii/"
    assert result["doorway_rationale"] == result["recommendation"]["rationale"]
    assert result["recommendation"]["title"] != "Sovereign Sensemaking Compass"


def test_doorway_selection_gold_star_and_transfer_review_are_reconciled():
    root = Path(__file__).resolve().parents[1]
    registry = json.loads((root / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    review = json.loads((root / "docs/qa/gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))
    benchmark_id = "general-guide-use-doorway-warrant-destination-selection-gold-star-2026-11-18"
    record = next(item for item in registry["records"] if item["benchmark_id"] == benchmark_id)
    transfer = next(item for item in review["entries"] if item["benchmark_id"] == benchmark_id)
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["doorway_status"] == "VERIFIED"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/the-living-archive-navigator-volume-iii/"
    assert record["rating_out_of_10"] == 10
    assert transfer["activation"] == "active_quality_contributor"
    assert transfer["reasoning_family"] == record["reasoning_family"]
    assert transfer["transferable_discipline"] == record["transferable_lesson"]
    assert transfer["abstention_boundary"] == record["transfer_boundary"]


def test_gold_star_uses_user_confirmed_live_render_as_canonical_successor_without_duplicate():
    root = Path(__file__).resolve().parents[1]
    registry = json.loads((root / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    benchmark_id = "general-guide-use-doorway-warrant-destination-selection-gold-star-2026-11-18"
    matches = [item for item in registry["records"] if item["benchmark_id"] == benchmark_id]
    assert len(matches) == 1
    record = matches[0]
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["live_render_verification"]["status"] == "USER_CONFIRMED_LIVE_RENDER"
    assert record["expected_response"].endswith("For this question, The Living Archive Navigator: Volume III – Knowledge & Sensemaking is the appropriate next destination.")
    assert "Continue Exploring" in " ".join(record["live_render_verification"]["visual_contract"])
    assert "systems thinking, discernment, and sensemaking" in record["expected_doorway"]["rationale"]
    assert record["numbering_status"] == "UNASSIGNED"
