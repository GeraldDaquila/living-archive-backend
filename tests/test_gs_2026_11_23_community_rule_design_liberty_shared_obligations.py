import json

import main
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ID = "gs-2026-11-23-community-rule-design-liberty-shared-obligations"


def test_community_rule_design_gold_star_is_registered_with_bounded_learning_and_verified_doorway():
    registry = json.loads((ROOT / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    fixture = json.loads((ROOT / "tests/fixtures/gs-2026-11-23-community-rule-design-liberty-shared-obligations.json").read_text(encoding="utf-8"))
    reviews = json.loads((ROOT / "docs/qa/gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))["entries"]
    transfer_map = json.loads((ROOT / "docs/qa/gold_star_transferability_map.json").read_text(encoding="utf-8"))
    record = next(item for item in registry["records"] if item["benchmark_id"] == BENCHMARK_ID)
    review = next(item for item in reviews if item["benchmark_id"] == BENCHMARK_ID)
    mapped = next(item for item in transfer_map["entries"] if item["benchmark_id"] == BENCHMARK_ID)

    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["explicit_user_elevation_approval"] is True
    assert record["query"] == fixture["query"]
    assert record["expected_response"] == fixture["expected_response"]
    assert record["expected_doorway"] == fixture["expected_doorway"]
    assert len(record["expected_response"].split("\n\n")) == 3
    assert record["doorway_status"] == "VERIFIED_CANONICAL_DESTINATION"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/2026/09/21/the-barangay-before-the-state-human-scale-governance-in-practice/"
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert record["numbering_status"] == "UNASSIGNED"
    assert review["activation"] == "active_quality_contributor"
    assert review["transferable_discipline"] == record["transferable_lesson"]
    assert mapped["family"] == record["reasoning_family"]
    assert mapped["structural_lesson"] == record["transferable_lesson"]
    assert "least restrictive workable means" in mapped["structural_lesson"]


def test_community_rule_design_selector_recognizes_decision_noun_in_unseen_question():
    query = (
        "When a community faces a difficult trade-off between individual freedom "
        "and shared responsibility, how should it make a decision that is both "
        "fair and workable?"
    )

    assert main._select_verified_doorway_conceptual_family(query) == (
        "community_rule_design_personal_liberty_shared_obligations"
    )


def test_community_rule_transfer_prompt_names_legitimate_purpose_and_evidence_before_limits():
    from general_guide_composition import _build_general_guide_system_prompt

    query = "How should a community decide whether limits on personal liberty are justified by shared obligations and risks?"
    prompt = _build_general_guide_system_prompt(query)
    assert "legitimate shared purpose" in prompt
    assert "evidence of harm or coordination need" in prompt
    assert "For community liberty limits" not in _build_general_guide_system_prompt("What is transparency?")
