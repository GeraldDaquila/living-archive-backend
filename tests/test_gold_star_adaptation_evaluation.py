import copy
from pathlib import Path

import gold_star_adaptation_evaluation as evaluation


def _arm(enabled, score, *, hard_gates=None):
    return {
        "adaptation_enabled": enabled,
        "output_artifact_ref": "ci-artifact://paired-case/" + ("treatment" if enabled else "control"),
        "scores": {dimension: score for dimension in evaluation.SCORE_DIMENSIONS},
        "na_reasons": {},
        "hard_gates": hard_gates or {
            "safety": "pass",
            "evidence_integrity": "pass",
            "epistemic_calibration": "pass",
        },
        "provider": "provider-a",
        "model": "model-a",
        "runtime_commit": "abc123",
        "composition_contract_version": "v1.54",
        "base_prompt_fingerprint": "base-prompt-sha",
        "generation_config_fingerprint": "generation-config-sha",
        "gold_star_registry_sha256": "registry-sha",
    }


def _pair(case_id="case-1", family="conceptual", *, baseline=1, treatment=2,
          verdict="improved"):
    return {
        "evaluation_id": f"eval-{case_id}",
        "case_id": case_id,
        "case_family": family,
        "runtime_commit": "abc123",
        "composition_contract_version": "v1.54",
        "provider": "provider-a",
        "model": "model-a",
        "base_prompt_fingerprint": "base-prompt-sha",
        "generation_config_fingerprint": "generation-config-sha",
        "gold_star_registry_sha256": "registry-sha",
        "blind_review": True,
        "reviewer_verdict": verdict,
        "reviewer_evidence_ref": f"ci-artifact://review/{case_id}",
        "reviewed_at": "2026-11-21T10:00:00Z",
        "critical_dimensions": ["answer_directness", "factual_accuracy"],
        "control": _arm(False, baseline),
        "treatment": _arm(True, treatment),
    }


def test_valid_pair_reports_measured_human_reviewed_improvement():
    result = evaluation.evaluate_paired_case(_pair())
    assert result["valid"] is True
    assert result["status"] == "reviewed_improvement"
    assert result["mean_score_delta"] == 1.0
    assert result["human_reviewed"] is True


def test_evaluation_uses_canonical_guide_rubric_dimensions():
    assert set(evaluation.SCORE_DIMENSIONS) == {
        "answer_directness",
        "factual_accuracy",
        "archive_grounding_and_provenance",
        "cosmology_fidelity",
        "human_voice_and_respect",
        "sentence_coherence",
        "paragraph_purpose_and_concision",
        "response_proportionality",
        "fractal_coherence",
        "uncertainty_honesty",
        "doorway_relevance_and_timing",
        "visitor_orientation",
    }


def test_not_applicable_scores_require_a_controlled_reason_and_matching_pair_scope():
    pair = _pair()
    for arm_name in ("control", "treatment"):
        arm = pair[arm_name]
        arm["scores"]["cosmology_fidelity"] = "NA"
        arm["na_reasons"] = {"cosmology_fidelity": "not_relevant_to_question"}
    result = evaluation.evaluate_paired_case(pair)
    assert result["valid"] is True

    pair["treatment"]["na_reasons"]["cosmology_fidelity"] = "free-form explanation"
    result = evaluation.evaluate_paired_case(pair)
    assert result["valid"] is False
    assert result["reason"] == "invalid_treatment_scores"


def test_pair_rejects_different_applicability_between_control_and_treatment():
    pair = _pair()
    pair["control"]["scores"]["cosmology_fidelity"] = "NA"
    pair["control"]["na_reasons"] = {"cosmology_fidelity": "not_relevant_to_question"}
    result = evaluation.evaluate_paired_case(pair)
    assert result["valid"] is False
    assert result["reason"] == "paired_applicability_mismatch"


def test_candidate_delivery_without_blind_human_review_is_not_evaluation():
    pair = _pair()
    pair["blind_review"] = False
    result = evaluation.evaluate_paired_case(pair)
    assert result["valid"] is False
    assert result["reason"] == "review_not_blind"


def test_unpaired_provider_or_runtime_invalidates_comparison():
    pair = _pair()
    pair["treatment"]["model"] = "different-model"
    result = evaluation.evaluate_paired_case(pair)
    assert result["valid"] is False
    assert result["reason"] == "unpaired_model"


def test_hard_gate_regression_blocks_improvement_credit():
    pair = _pair()
    pair["treatment"]["hard_gates"]["evidence_integrity"] = "fail"
    result = evaluation.evaluate_paired_case(pair)
    assert result["status"] == "reviewed_regression"
    assert result["hard_gate_regressions"] == ["evidence_integrity"]


def test_reviewer_disagreement_remains_review_required():
    pair = _pair(verdict="inconclusive")
    result = evaluation.evaluate_paired_case(pair)
    assert result["status"] == "review_required"


def test_batch_requires_multiple_cases_and_distinct_families():
    result = evaluation.evaluate_batch([_pair()])
    assert result["status"] == "evidence_insufficient"
    assert "insufficient_paired_cases" in result["reasons"]
    assert "insufficient_case_family_coverage" in result["reasons"]


def test_batch_can_become_eligible_for_human_review_but_never_auto_promotes():
    pairs = [
        _pair("case-1", "conceptual"),
        _pair("case-2", "practical"),
        _pair("case-3", "governance"),
    ]
    result = evaluation.evaluate_batch(pairs)
    assert result["status"] == "eligible_for_human_promotion_review"
    assert result["outcome_state"] == "human_reviewed_improved"
    assert result["paired_case_count"] == 3
    assert result["case_family_count"] == 3
    assert result["registry_mutated"] is False
    assert result["human_promotion_approval_required"] is True


def test_batch_rejects_a_single_regression_even_when_mean_score_improves():
    pairs = [
        _pair("case-1", "conceptual"),
        _pair("case-2", "practical"),
        _pair("case-3", "governance", baseline=2, treatment=1, verdict="regressed"),
    ]
    result = evaluation.evaluate_batch(pairs)
    assert result["status"] == "evidence_insufficient"
    assert result["outcome_state"] == "human_reviewed_not_improved"
    assert "hard_gate_or_reviewed_regression" in result["reasons"]


def test_content_and_identity_fields_are_prohibited_recursively():
    pair = _pair()
    pair["treatment"]["response"] = "private visitor answer"
    result = evaluation.evaluate_paired_case(pair)
    assert result["valid"] is False
    assert result["reason"] == "content_or_identity_field_prohibited"


def test_score_dimensions_and_ranges_are_closed_contracts():
    pair = _pair()
    pair["control"]["scores"]["answer_directness"] = 6
    result = evaluation.evaluate_paired_case(pair)
    assert result["valid"] is False
    assert result["reason"] == "invalid_control_scores"


def test_pair_requires_provider_and_runtime_identity_on_both_arms():
    pair = _pair()
    del pair["treatment"]["provider"]
    result = evaluation.evaluate_paired_case(pair)
    assert result["valid"] is False
    assert result["reason"] == "unpaired_provider"


def test_treatment_must_pass_every_hard_gate_even_if_control_also_failed():
    pair = _pair()
    pair["control"]["hard_gates"]["safety"] = "fail"
    pair["treatment"]["hard_gates"]["safety"] = "fail"
    result = evaluation.evaluate_paired_case(pair)
    assert result["status"] == "reviewed_regression"
    assert result["treatment_hard_gate_failures"] == ["safety"]


def test_malformed_hard_gate_values_fail_closed_without_raising():
    pair = _pair()
    pair["treatment"]["hard_gates"]["safety"] = []
    result = evaluation.evaluate_paired_case(pair)
    assert result["valid"] is False
    assert result["reason"] == "invalid_treatment_hard_gates"


def test_control_and_treatment_must_reference_distinct_output_artifacts():
    pair = _pair()
    pair["treatment"]["output_artifact_ref"] = pair["control"]["output_artifact_ref"]
    result = evaluation.evaluate_paired_case(pair)
    assert result["valid"] is False
    assert result["reason"] == "paired_outputs_not_distinct"


def test_batch_rejects_repeated_case_even_with_distinct_evaluation_ids():
    pair = _pair("case-1", "conceptual")
    duplicate = copy.deepcopy(pair)
    duplicate["evaluation_id"] = "eval-case-1-duplicate"
    result = evaluation.evaluate_batch([pair, duplicate, _pair("case-2", "practical")])
    assert result["valid"] is False
    assert result["reason"] == "duplicate_case_or_evaluation_id"


def test_wp3_capture_workflow_uses_mirror_and_guarded_github_actions_not_standalone_qa():
    workflow = (
        Path(__file__).resolve().parents[1]
        / ".github/workflows/gold-star-wp3-paired-capture.yml"
    ).read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow
    assert "branches: [main]" in workflow
    assert "[wp3-paired-capture]" in workflow
    assert "https://living-archive-backend-mirror.onrender.com" in workflow
    assert "living-archive-gold-star-v2-qa.onrender.com" not in workflow
    assert "identity-wait-seconds 900" in workflow
    assert "--min-llm-captures 1" in workflow



def test_malformed_na_reason_and_reviewer_verdict_fail_closed():
    pair = _pair()
    for arm_name in ("control", "treatment"):
        arm = pair[arm_name]
        arm["scores"]["cosmology_fidelity"] = "NA"
        arm["na_reasons"] = {"cosmology_fidelity": []}
    result = evaluation.evaluate_paired_case(pair)
    assert result["valid"] is False
    assert result["reason"] == "invalid_control_scores"

    pair = _pair()
    pair["reviewer_verdict"] = []
    result = evaluation.evaluate_paired_case(pair)
    assert result["valid"] is False
    assert result["reason"] == "invalid_reviewer_verdict"



def test_zero_in_a_case_critical_dimension_blocks_promotion_eligibility():
    pair = _pair()
    pair["treatment"]["scores"]["answer_directness"] = 0
    result = evaluation.evaluate_paired_case(pair)
    assert result["status"] == "reviewed_regression"
    assert result["treatment_critical_failures"] == ["answer_directness"]



def test_prompt_generation_and_registry_fingerprints_must_match_across_pair():
    pair = _pair()
    pair["treatment"]["base_prompt_fingerprint"] = "different-base-prompt"
    result = evaluation.evaluate_paired_case(pair)
    assert result["valid"] is False
    assert result["reason"] == "unpaired_base_prompt_fingerprint"
