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


EXTRAORDINARY_CLAIMS_QUERY = "How should the Guide respond to extraordinary claims?"


def test_extraordinary_claims_select_the_canonical_levels_of_claim_page():
    family = main._select_verified_doorway_conceptual_family(EXTRAORDINARY_CLAIMS_QUERY)

    assert family == "extraordinary_claim_discernment"
    doorway = main._VERIFIED_CONCEPTUAL_FAMILY_DOORWAYS[family]
    assert doorway["title"] == "Levels of Claim"
    assert doorway["url"] == "https://geralddaquila.com/levels-of-claim/"
    assert "observation, interpretation, explanation" in doorway["rationale"]
    assert "evidential weight" in doorway["rationale"]


def test_extraordinary_claims_restore_doorway_over_a_broad_upstream_candidate():
    broad_candidate = {
        "title": "The Sovereign Sensemaking Compass",
        "url": "https://geralddaquila.com/the-sovereign-sensemaking-compass/",
        "rationale": "A broad orientation resource.",
    }
    result = main._guide_restore_verified_doorway(
        {"response": "A complete answer.", "recommendation": broad_candidate},
        EXTRAORDINARY_CLAIMS_QUERY,
    )

    assert result["recommendation"]["title"] == "Levels of Claim"
    assert result["recommendation"]["url"] == "https://geralddaquila.com/levels-of-claim/"
    assert result["canonical_doorway"] == result["recommendation"]
    assert result["authoritative_doorway"] == result["recommendation"]
    assert result["doorway_selection_status"] == "VERIFIED_RELEVANT_DESTINATION"
    assert result["doorway_selection_evaluated"] is True
    assert result["doorway_selection_source"] == "reviewed_extraordinary_claim_discernment_family"
    assert result["doorway_omission_reason"] is None


def test_extraordinary_claim_doorway_requires_an_evaluation_task_and_not_just_claim_language():
    assert main._select_verified_doorway_conceptual_family(
        "What extraordinary claims appeared in the historical record?"
    ) is None
    assert main._select_verified_doorway_conceptual_family(
        "How do insurance claims work?"
    ) is None


def test_explicit_no_doorway_instruction_still_overrides_extraordinary_claim_family():
    query = EXTRAORDINARY_CLAIMS_QUERY + " Please do not include links or resources."
    assert main._select_verified_doorway_conceptual_family(query) is None
    result = main._guide_enforce_terminal_doorway_policy(
        {"response": "A complete answer.", "recommendation": main._VERIFIED_CONCEPTUAL_FAMILY_DOORWAYS["extraordinary_claim_discernment"]},
        query,
    )
    assert result.get("recommendation") is None
    assert result["doorway_decision"] == "omit"
    assert result["doorway_selection_status"] == "AUTHORIZED_OMISSION"
