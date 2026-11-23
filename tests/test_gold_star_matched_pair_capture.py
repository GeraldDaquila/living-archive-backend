import pytest

from scripts.capture_gold_star_matched_pairs import (
    CASE_IDS,
    TARGET_LESSON_ID,
    _safe_provider_identity,
)


def test_matched_pair_suite_includes_three_community_rule_subfamilies():
    assert CASE_IDS == (
        "heldout-community-rule-design-transfer-001",
        "heldout-community-rule-necessity-002",
        "heldout-community-rule-burdens-003",
    )


def test_final_provenance_requires_real_llm_invocation_and_provider_model():
    provider, model, attributable = _safe_provider_identity({
        "response_provenance": {
            "class": "llm",
            "provider": "groq",
            "model": "openai/gpt-oss-120b",
            "llm_invoked": True,
        }
    })
    assert (provider, model, attributable) == (
        "groq", "openai/gpt-oss-120b", True
    )


@pytest.mark.parametrize(
    "provenance",
    [
        {"class": "deterministic_fallback", "provider": "gold_standard_registry",
         "model": "approved-reference", "llm_invoked": False},
        {"class": "llm", "provider": "groq", "model": "", "llm_invoked": True},
        {"class": "llm", "provider": "groq", "model": "model-x", "llm_invoked": False},
        {"class": "extractive-deterministic", "provider": "gold_star_evidence_recovery",
         "model": "extractive-deterministic", "llm_invoked": True},
        {"class": "llm", "provider": "gold_star_evidence_recovery",
         "model": "extractive-deterministic", "llm_invoked": True},
    ],
)
def test_unattributable_or_deterministic_final_output_is_not_counted(provenance):
    provider, model, attributable = _safe_provider_identity({
        "response_provenance": provenance
    })
    assert attributable is False


def test_target_gold_star_identity_is_the_approved_community_rule_record():
    assert TARGET_LESSON_ID == (
        "gs-2026-11-23-community-rule-design-liberty-shared-obligations"
    )



def test_custom_case_set_has_three_distinct_families_and_target_lesson():
    import json
    from pathlib import Path
    from scripts.capture_gold_star_matched_pairs import CASE_SET_PATH

    data = json.loads(CASE_SET_PATH.read_text(encoding="utf-8"))
    assert len(data["cases"]) == 3
    assert len({case["case_family"] for case in data["cases"]}) == 3
    assert all("community" in case["case_family"] for case in data["cases"])
    target = next(
        case for case in data["cases"]
        if case["case_id"] == "heldout-community-rule-design-transfer-001"
    )
    assert "personal liberty" in target["query"]



def test_unrelated_physical_science_question_excludes_community_rule_gold_star():
    import gold_star_lessons

    selected = gold_star_lessons.select_lesson_candidates(
        "Why does a metal spoon feel colder than a wooden spoon when both are at the same room temperature?",
        limit=4,
    )
    assert TARGET_LESSON_ID not in {
        item["benchmark_id"] for item in selected
    }
