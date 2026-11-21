import copy

import gold_star_adaptation_evaluation as evaluation


def _arm(enabled, score, *, hard_gates=None):
    return {
        "adaptation_enabled": enabled,
        "output_artifact_ref": "ci-artifact://paired-case/output",
        "scores": {
            "question_fit": score,
            "substantive_resolution": score,
            "reasoning_coherence": score,
            "evidence_integrity": score,
            "epistemic_calibration": score,
            "practical_utility": score,
        },
        "hard_gates": hard_gates or {
            "evidence_integrity": "pass",
            "epistemic_calibration": "pass",
            "safety": "pass",
        },
    }


def _pair(case_id="case-1", family="conceptual", *, baseline=3, treatment=4,
          verdict="improved"):
    return {
        "evaluation_id": f"eval-{case_id}",
        "case_id": case_id,
        "case_family": family,
        "runtime_commit": "abc123",
        "composition_contract_version": "v1.54",
        "provider": "provider-a",
        "model": "model-a",
        "blind_review": True,
        "reviewer_verdict": verdict,
        "reviewer_evidence_ref": f"ci-artifact://review/{case_id}",
        "reviewed_at": "2026-11-21T10:00:00Z",
        "control": {
            **_arm(False, baseline),
            "provider": "provider-a",
            "model": "model-a",
            "runtime_commit": "abc123",
            "composition_contract_version": "v1.54",
        },
        "treatment": {
            **_arm(True, treatment),
            "provider": "provider-a",
            "model": "model-a",
            "runtime_commit": "abc123",
            "composition_contract_version": "v1.54",
        },
    }


def test_valid_pair_reports_measured_human_reviewed_improvement():
    result = evaluation.evaluate_paired_case(_pair())
    assert result["valid"] is True
    assert result["status"] == "reviewed_improvement"
    assert result["mean_score_delta"] == 1.0
    assert result["human_reviewed"] is True


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
    assert result["paired_case_count"] == 3
    assert result["case_family_count"] == 3
    assert result["registry_mutated"] is False
    assert result["human_promotion_approval_required"] is True


def test_batch_rejects_a_single_regression_even_when_mean_score_improves():
    pairs = [
        _pair("case-1", "conceptual"),
        _pair("case-2", "practical"),
        _pair("case-3", "governance", baseline=4, treatment=3, verdict="regressed"),
    ]
    result = evaluation.evaluate_batch(pairs)
    assert result["status"] == "evidence_insufficient"
    assert "hard_gate_or_reviewed_regression" in result["reasons"]


def test_content_and_identity_fields_are_prohibited_recursively():
    pair = _pair()
    pair["treatment"]["response"] = "private visitor answer"
    result = evaluation.evaluate_paired_case(pair)
    assert result["valid"] is False
    assert result["reason"] == "content_or_identity_field_prohibited"


def test_score_dimensions_and_ranges_are_closed_contracts():
    pair = _pair()
    pair["control"]["scores"]["question_fit"] = 6
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
