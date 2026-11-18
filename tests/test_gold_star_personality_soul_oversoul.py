import json
from pathlib import Path


def test_personality_soul_oversoul_question_has_exact_provider_independent_gold_star():
    query = "What is the difference between what my personality wants, what my soul is learning, and what my Oversoul may be inviting me to become?"
    registry = json.loads(Path("docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "gs-2026-11-18-personality-soul-oversoul-discernment"
    )

    from deterministic_answer_recovery import (
        compose_recovery,
        has_registered_recovery,
        is_personality_soul_oversoul_question,
        registered_recovery_recommendation,
    )

    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == query
    assert record["explicit_user_elevation_approval"] is True
    assert record["freeze_policy"] == "immutable_user_approved_gold_standard"
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["gold_star_capabilities"]["exact_answer_authority"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is True
    assert is_personality_soul_oversoul_question(query)
    assert has_registered_recovery(query)
    assert compose_recovery(query) == record["expected_response"]
    assert len(record["expected_response"].split("\n\n")) == 3
    for phrase in ("personality", "soul is learning", "Oversoul", "not a command", "without surrendering your judgment"):
        assert phrase.casefold() in record["expected_response"].casefold()
    assert registered_recovery_recommendation(query) == record["expected_doorway"]
    assert record["expected_doorway"]["title"] == "Eternal / Oversoul Law – The Immutable Jurisdiction"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/oversoul-law"

    import main
    deterministic = main._basic_inquiry_round1_deterministic_response(
        query, {}, {"context_blocks": ""}, recommendation_available=False
    )
    assert deterministic["response"] == record["expected_response"]
    assert deterministic["recommendation"] == record["expected_doorway"]
    assert deterministic["canonical_doorway"] == record["expected_doorway"]


def test_personality_soul_oversoul_classifier_rejects_adjacent_questions():
    from deterministic_answer_recovery import is_personality_soul_oversoul_question

    assert not is_personality_soul_oversoul_question(
        "What does my personality want, and how can I make a better decision?"
    )
    assert not is_personality_soul_oversoul_question(
        "What is the difference between soul learning and spiritual purpose?"
    )
    assert not is_personality_soul_oversoul_question(
        "What is the difference between my personality and my soul?"
    )


def test_personality_soul_oversoul_gold_star_has_bounded_transfer_review():
    benchmark = "gs-2026-11-18-personality-soul-oversoul-discernment"
    reviews = json.loads(Path("docs/qa/gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))
    review = next(item for item in reviews["entries"] if item["benchmark_id"] == benchmark)
    assert review["activation"] == "active_quality_contributor"
    assert "three lenses" in review["transferable_discipline"]
    assert "lived evidence" in review["transferable_discipline"]
    assert "not independently verified facts" in review["transferable_discipline"]
    assert "do not transfer this answer text or doorway" in review["abstention_boundary"]
