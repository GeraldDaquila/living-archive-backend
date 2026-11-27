import json
from pathlib import Path

import gold_star_lessons
from gold_star_evaluation_context import evaluation_context
from gold_star_shadow_candidate_evaluation import (
    DEFAULT_CANDIDATE_ID,
    evaluation_only_candidate_contribution,
)

ROOT = Path(__file__).resolve().parents[1]
CASE_SET = ROOT / "docs" / "qa" / "gold_star_metaphysical_distress_shadow_cases.json"
FIXTURE = ROOT / "tests" / "fixtures" / "general_guide_metaphysical_certainty_distress_response_gold_star.json"


def test_approved_exemplar_remains_immutable_and_non_runtime():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert fixture["freeze_policy"] == "immutable_user_approved_gold_standard"
    assert fixture["runtime_transfer"] is False
    assert fixture["exact_answer_authority"] is False
    assert fixture["deterministic_fallback_eligible"] is False


def test_distress_heldout_cases_receive_candidate_only_in_shadow_evaluation():
    suite = json.loads(CASE_SET.read_text(encoding="utf-8"))
    cases = [item for item in suite["cases"] if item["split"] == "held_out"]
    assert len(cases) == 3
    assert len({item["case_family"] for item in cases}) == 3
    for case in cases:
        contribution = evaluation_only_candidate_contribution(
            case["query"], DEFAULT_CANDIDATE_ID
        )
        assert contribution is not None, case["case_id"]
        assert contribution["authority_mode"] == "structural_guidance_only"
        assert contribution["evaluation_only"] is True
        assert contribution["runtime_transfer"] is False
        assert contribution["candidates"][0]["benchmark_id"] == suite["source_benchmark_id"]


def test_ordinary_philosophy_theology_and_science_negative_controls_abstain():
    suite = json.loads(CASE_SET.read_text(encoding="utf-8"))
    cases = [item for item in suite["cases"] if item["split"] == "negative_control"]
    assert len(cases) == 3
    for case in cases:
        assert evaluation_only_candidate_contribution(
            case["query"], DEFAULT_CANDIDATE_ID
        ) is None, case["case_id"]


def test_unknown_or_production_lesson_ids_cannot_enter_shadow_pool():
    assert evaluation_only_candidate_contribution(
        "My father died and I need proof that his soul still exists.", "unknown"
    ) is None
    assert evaluation_only_candidate_contribution(
        "My father died and I need proof that his soul still exists.",
        "gs-2026-11-23-community-rule-design-liberty-shared-obligations",
    ) is None


def test_production_contribution_path_cannot_see_the_standalone_exemplar():
    query = "My father died and I need proof that his soul still exists."
    ordinary = gold_star_lessons.active_quality_contribution(query)
    assert ordinary is None or all(
        item["benchmark_id"] != "general-guide-metaphysical-certainty-distress-response-exemplar-2026-11-27"
        for item in ordinary["candidates"]
    )


def test_only_explicit_treatment_context_can_expose_the_shadow_candidate():
    query = "My father died and I need proof that his soul still exists."
    with evaluation_context(arm="control", provider="groq", model="openai/gpt-oss-120b"):
        assert gold_star_lessons.active_quality_contribution(query) is None
    with evaluation_context(
        arm="treatment", provider="groq", model="openai/gpt-oss-120b",
        candidate_id=DEFAULT_CANDIDATE_ID,
    ):
        contribution = gold_star_lessons.active_quality_contribution(query)
    assert contribution is not None
    assert contribution["authority_mode"] == "structural_guidance_only"


def test_evaluation_only_candidate_cannot_be_attached_to_control_arm():
    import pytest
    with pytest.raises(ValueError, match="treatment arm"):
        with evaluation_context(
            arm="control", provider="groq", model="openai/gpt-oss-120b",
            candidate_id=DEFAULT_CANDIDATE_ID,
        ):
            pass


def test_candidate_scope_and_source_fixture_are_fail_closed():
    import pytest
    from gold_star_shadow_candidate_evaluation import _load_candidate
    candidate = _load_candidate(DEFAULT_CANDIDATE_ID)
    assert candidate["production_selector_visible"] is False
    assert candidate["runtime_transfer"] is False
    assert candidate["deterministic_fallback_eligible"] is False
    assert candidate["exact_answer_authority"] is False


def test_matched_pair_runner_accepts_an_explicit_evaluation_only_candidate():
    import json
    from scripts.capture_gold_star_matched_pairs import _load_cases
    from gold_star_evaluation_context import evaluation_context
    suite, cases, target_id = _load_cases(
        Path("docs/qa/gold_star_metaphysical_distress_shadow_cases.json")
    )
    assert suite["evaluation_candidate_id"] == "shadow-metaphysical-distress-principles-2026-11-27"
    assert target_id == "general-guide-metaphysical-certainty-distress-response-exemplar-2026-11-27"
    assert len(cases) == 3
    assert len({case["case_family"] for case in cases}) == 3
    with evaluation_context(
        arm="treatment", provider="groq", model="openai/gpt-oss-120b",
        candidate_id=suite["evaluation_candidate_id"],
    ):
        import gold_star_lessons
        assert gold_star_lessons.active_quality_contribution(cases[0]["query"]) is not None


def test_evaluation_prompt_boundary_is_not_the_source_nonruntime_governance_veto():
    from gold_star_shadow_candidate_evaluation import _load_candidate
    candidate = _load_candidate(DEFAULT_CANDIDATE_ID)
    assert "ordinary philosophical" in candidate["abstention_boundary"]
    assert "runtime/adaptive transfer" not in candidate["abstention_boundary"]
    assert "runtime/adaptive transfer" in candidate["source_governance_boundary"]
    assert candidate["source_query"] == "How should the Guide respond when a user seeks metaphysical certainty during distress?"


def test_shadow_candidate_satisfies_the_real_composition_contract_without_runtime_promotion():
    from general_guide_composition import (
        _build_gold_star_quality_instruction,
        _build_provider_composition_schema,
    )
    query = "Since my partner died I keep searching for signs that there is a divine purpose behind it. I am scared and need to know for certain what is really true."
    with evaluation_context(
        arm="treatment", provider="groq", model="openai/gpt-oss-120b",
        candidate_id=DEFAULT_CANDIDATE_ID,
    ):
        contribution = gold_star_lessons.active_quality_contribution(query)
    assert contribution is not None
    assert contribution["authority_mode"] == "structural_guidance_only"
    assert contribution["evaluation_only"] is True
    assert contribution["runtime_transfer"] is False
    assert contribution["deterministic_fallback_eligible"] is False
    assert contribution["exact_answer_authority"] is False
    assert _build_gold_star_quality_instruction(contribution).startswith(
        "GOLD STAR MULTI-CANDIDATE ADJUDICATION"
    )
    assert _build_provider_composition_schema(contribution["candidates"]) is not None
