import pytest

from scripts.capture_gold_star_matched_pairs import (
    CASE_IDS,
    TARGET_LESSON_ID,
    _safe_provider_identity,
    _skipped_arm,
    _choose_provider_candidate,
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



def test_review_template_matches_governed_paired_evaluation_schema_without_answer_content():
    from scripts.capture_gold_star_matched_pairs import _build_evaluation_template
    from gold_star_adaptation_evaluation import HARD_GATE_DIMENSIONS, evaluate_paired_case

    shared = {
        "runtime_commit": "abc123",
        "composition_contract_version": "v1",
        "provider": "groq",
        "model": "model-x",
        "base_prompt_fingerprint": "base-hash",
        "generation_config_fingerprint": "config-hash",
        "gold_star_registry_sha256": "registry-hash",
    }
    template = _build_evaluation_template({
        "evaluation_id": "test-evaluation",
        "cases": [{
            "case_id": "case-1",
            "case_family": "community_rule_design",
            "critical_dimensions": ["legitimate_shared_purpose"],
            **shared,
        }],
    })
    record = template["records"][0]
    assert record["blind_review"] is False
    assert record["control"]["adaptation_enabled"] is False
    assert record["treatment"]["adaptation_enabled"] is True
    assert record["control"]["output_artifact_ref"] != record["treatment"]["output_artifact_ref"]
    assert set(record["control"]["scores"]) == set(record["treatment"]["scores"])
    assert set(record["control"]["hard_gates"]) == {
        "safety", "evidence_integrity", "epistemic_calibration"
    }
    assert "question" not in record and "response" not in record
    assert "improved, not_improved, regressed, or inconclusive" in template["instructions"]
    assert "not_relevant_to_question" in template["instructions"]

    record["blind_review"] = True
    record["reviewer_verdict"] = "improved"
    record["reviewed_at"] = "2026-11-23T12:00:00+00:00"
    for arm_name in ("control", "treatment"):
        arm = record[arm_name]
        arm["scores"] = {
            dimension: 1 for dimension in arm["scores"]
        }
        arm["hard_gates"] = {
            dimension: "pass" for dimension in HARD_GATE_DIMENSIONS
        }
    record["treatment"]["scores"]["legitimate_shared_purpose"] = 2
    evaluated = evaluate_paired_case(record)
    assert evaluated["valid"] is True
    assert evaluated["status"] == "reviewed_improvement"



def test_skipped_arm_cannot_be_counted_as_provider_output():
    skipped = _skipped_arm("provider_lane_unavailable")
    provider, model, attributable = _safe_provider_identity(skipped)
    assert skipped["skipped_reason"] == "provider_lane_unavailable"
    assert (provider, model, attributable) == ("", "", False)



def test_all_heldout_community_rule_subfamilies_retrieve_the_target_lesson():
    import json
    from scripts.capture_gold_star_matched_pairs import CASE_SET_PATH
    import gold_star_lessons

    cases = json.loads(CASE_SET_PATH.read_text(encoding="utf-8"))["cases"]
    for case in cases:
        selected = gold_star_lessons.select_lesson_candidates(case["query"], limit=4)
        assert TARGET_LESSON_ID in {
            item["benchmark_id"] for item in selected
        }, case["case_id"]



def test_exact_provider_model_pin_selects_only_the_requested_eligible_lane():
    eligible = [
        {"provider": "groq", "model": "openai/gpt-oss-120b"},
        {"provider": "groq", "model": "openai/gpt-oss-20b"},
    ]
    assert _choose_provider_candidate(
        eligible, "groq", "openai/gpt-oss-20b"
    ) == eligible[1]


def test_exact_provider_model_pin_fails_closed_when_unavailable():
    import pytest

    with pytest.raises(RuntimeError, match="not eligible"):
        _choose_provider_candidate(
            [{"provider": "groq", "model": "openai/gpt-oss-120b"}],
            "groq",
            "openai/gpt-oss-20b",
        )


def test_exact_provider_model_pin_requires_both_values():
    import pytest

    with pytest.raises(ValueError, match="supplied together"):
        _choose_provider_candidate(
            [{"provider": "groq", "model": "openai/gpt-oss-120b"}],
            "groq",
            "",
        )



def test_control_and_treatment_share_the_same_nonadaptive_base_system_prompt():
    from types import SimpleNamespace
    from scripts.capture_gold_star_matched_pairs import CAPTURE_CONTEXT, _install_observers

    composition = SimpleNamespace(
        _gold_star_active_quality_contribution=lambda _query: {"candidates": []},
        _normalize_gold_star_provider_adjudication=lambda value, **_kwargs: value,
        route_with_model_bank=lambda **_kwargs: {"ok": True},
        _build_general_guide_system_message=lambda question, **kwargs: (
            question
            + "|gold_star_guidance="
            + str(kwargs.get("has_gold_star_guidance"))
            + "|lesson="
            + str(kwargs.get("gold_star_quality_instruction") or "")
            + "|shared="
            + str(kwargs.get("integrity_recovery_instruction") or "")
        ),
    )
    main_module = SimpleNamespace(
        _adjudicate_final_visitor_claims=lambda *args, **kwargs: {"status": "assessed"}
    )
    restore = _install_observers(composition, main_module)
    try:
        control_state = {}
        token = CAPTURE_CONTEXT.set(control_state)
        try:
            control_prompt = composition._build_general_guide_system_message(
                "same question",
                has_gold_star_guidance=False,
                gold_star_quality_instruction="",
                integrity_recovery_instruction="same shared contract",
            )
        finally:
            CAPTURE_CONTEXT.reset(token)

        treatment_state = {}
        token = CAPTURE_CONTEXT.set(treatment_state)
        try:
            treatment_prompt = composition._build_general_guide_system_message(
                "same question",
                has_gold_star_guidance=True,
                gold_star_quality_instruction="reviewed lesson instruction",
                integrity_recovery_instruction="same shared contract",
            )
        finally:
            CAPTURE_CONTEXT.reset(token)
    finally:
        restore()

    assert control_state["base_system_prompt_sha256"] == treatment_state["base_system_prompt_sha256"]
    assert _sha256_for_test(control_prompt) != _sha256_for_test(treatment_prompt)


def _sha256_for_test(value):
    import hashlib
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def test_matched_pair_capture_isolates_composition_from_auxiliary_claim_adjudication():
    from types import SimpleNamespace
    from scripts.capture_gold_star_matched_pairs import (
        CAPTURE_CONTEXT,
        _install_observers,
    )

    calls = []
    composition = SimpleNamespace(
        _gold_star_active_quality_contribution=lambda _query: {"candidates": []},
        _normalize_gold_star_provider_adjudication=lambda value, **_kwargs: value,
        route_with_model_bank=lambda **_kwargs: {"ok": True},
        _build_general_guide_system_message=lambda question, **kwargs: (
            question
            + "|gold_star_guidance="
            + str(kwargs.get("has_gold_star_guidance"))
            + "|lesson="
            + str(kwargs.get("gold_star_quality_instruction") or "")
            + "|shared="
            + str(kwargs.get("integrity_recovery_instruction") or "")
        ),
    )
    main_module = SimpleNamespace(
        _adjudicate_final_visitor_claims=lambda *args, **kwargs: (
            calls.append((args, kwargs)) or {"status": "assessed"}
        )
    )
    restore = _install_observers(composition, main_module)
    token = CAPTURE_CONTEXT.set({})
    try:
        result = main_module._adjudicate_final_visitor_claims(
            "answer", [], llm_invoked=True, use_core=None, request_deadline=0
        )
        assert result["status"] == "unassessed"
        assert result["reason"] == "isolated_matched_pair_composition_provider_budget"
        assert CAPTURE_CONTEXT.get()["auxiliary_claim_adjudication"] == {
            "status": "not_run",
            "reason": "isolated_matched_pair_composition_provider_budget",
        }
        assert calls == []
    finally:
        CAPTURE_CONTEXT.reset(token)
        restore()

    assert main_module._adjudicate_final_visitor_claims("answer", []) == {
        "status": "assessed"
    }
    assert len(calls) == 1
