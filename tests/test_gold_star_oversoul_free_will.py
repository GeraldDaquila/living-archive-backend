import json
from pathlib import Path


def test_user_approved_oversoul_free_will_gold_star_is_frozen_and_bounded():
    registry = json.loads(Path("docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "gs-2026-11-17-oversoul-free-will-influence-without-compulsion"
    )
    query = "What power does the Oversoul have over a person’s choice without undermining free will?"

    from deterministic_answer_recovery import (
        compose_recovery,
        is_oversoul_free_will_question,
        registered_recovery_recommendation,
    )

    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == query
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["freeze_policy"] == "immutable_user_approved_gold_standard"
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert is_oversoul_free_will_question(query)
    assert compose_recovery(query) == record["expected_response"]
    assert len(record["expected_response"].split("\\n\\n")) == 3
    assert record["expected_doorway"] == registered_recovery_recommendation(query)
    assert record["expected_doorway"]["title"] == "Eternal / Oversoul Law – The Immutable Jurisdiction"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/oversoul-law"
    assert "not independent evidence" in record["expected_doorway"]["rationale"]


def test_oversoul_free_will_gold_star_has_a_bounded_structural_transfer_review():
    registry = json.loads(Path("docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "gs-2026-11-17-oversoul-free-will-influence-without-compulsion"
    )
    reviews = json.loads(Path("docs/qa/gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))
    review = next(item for item in reviews["entries"] if item["benchmark_id"] == record["benchmark_id"])

    assert review["activation"] == "active_quality_contributor"
    assert "influence" in review["transferable_discipline"]
    assert "coercive determination" in review["transferable_discipline"]
    assert "independently verified facts" in review["transferable_discipline"]
    assert "never this answer text or its doorway" in review["abstention_boundary"]
