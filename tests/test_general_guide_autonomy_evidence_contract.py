"""Regression tests for task-specific evaluation of Guide capability claims."""

import general_guide_composition as guide
from pathlib import Path

MAIN_SOURCE = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")


def test_autonomy_question_is_routed_to_an_evidence_evaluation_framework():
    contract = guide._GENERAL_GUIDE_SYSTEM_COMPACT.lower()

    assert "recognize an evidence-evaluation task" in contract
    assert "continued operation and response volume demonstrate activity or continuity" in contract
    assert "not by themselves autonomy, adaptation, resilience, or improved answer quality" in contract
    assert "do not turn it into a reflective discussion" in contract


def test_four_capability_claims_require_distinct_evidence():
    contract = guide._GENERAL_GUIDE_SYSTEM_COMPACT.lower()

    for capability in ("autonomy:", "adaptivity:", "resilience:", "improvement:"):
        assert capability in contract

    assert "human interventions, overrides, escalations" in contract
    assert "held-out and unfamiliar cases" in contract
    assert "safe degradation, recovery" in contract
    assert "versioned baseline and follow-up evaluations" in contract
    assert "regression rates" in contract


def test_evidence_credibility_requires_auditable_comparison_and_limits():
    contract = guide._GENERAL_GUIDE_SYSTEM_COMPACT.lower()

    assert "observation period" in contract
    assert "task population and denominator" in contract
    assert "human-intervention rate" in contract
    assert "negative controls and regressions" in contract
    assert "protecting visitor privacy" in contract
    assert "distinguish directly observed results from inference and untested claims" in contract
    assert "do not invent thresholds, measurements, benchmark results" in contract


def test_absent_operational_data_cannot_be_presented_as_proof_of_actual_autonomy():
    contract = guide._GENERAL_GUIDE_SYSTEM_COMPACT.lower()

    assert "if the visitor supplies no operational data" in contract
    assert "say that the claim remains unverified" in contract
    assert "do not imply that the guide's actual autonomy or improvement has been established" in contract


def test_evaluation_answer_may_use_a_compact_table_instead_of_reflective_prose():
    contract = guide._GENERAL_GUIDE_SYSTEM_COMPACT.lower()

    assert "use a compact table or clearly separated criteria" in contract
    assert "the decision-relevant standard" in contract



def test_exact_guide_question_matches_provider_independent_recovery():
    question = (
        "The Guide has been operating successfully for an extended period without human intervention. "
        "What evidence should demonstrate that it is genuinely autonomous, adaptive, resilient, "
        "and improving rather than merely continuing to produce responses?"
    )
    recovery = guide._autonomy_evidence_evaluation_recovery(question)
    assert recovery is not None
    assert guide._has_autonomy_evidence_evaluation(recovery["response"])
    assert recovery["doorway_title"] == ""
    assert recovery["doorway_url"] == ""


def test_capability_evidence_recovery_covers_each_distinct_claim_and_limits():
    question = (
        "What evidence would demonstrate that the Guide is autonomous, adaptive, resilient, "
        "and improving rather than merely continuing to run?"
    )
    answer = guide._autonomy_evidence_evaluation_recovery(question)["response"]
    assert "human intervention" in answer
    assert "held-out cases" in answer
    assert "degrades safely" in answer
    assert "baseline and follow-up" in answer
    assert "regression rates" in answer
    assert "claims remain unverified" in answer


def test_predicate_does_not_capture_unrelated_autonomy_or_resilience_questions():
    assert not guide._requires_autonomy_evidence_evaluation(
        "How can a community become more resilient and adaptive?"
    )
    assert not guide._requires_autonomy_evidence_evaluation(
        "What does autonomy mean in political philosophy?"
    )


def test_incomplete_provider_answer_fails_the_evidence_contract():
    assert not guide._has_autonomy_evidence_evaluation(
        "The Guide has been running for a long time and has produced many responses."
    )



def test_basic_inquiry_uses_deterministic_recovery_before_provider_or_retrieval():
    start = MAIN_SOURCE.index("def _basic_inquiry_response(")
    end = MAIN_SOURCE.index("def _v48831_basic_inquiry_seam_self_audit(", start)
    block = MAIN_SOURCE[start:end]
    recovery = block.index("_autonomy_evidence_evaluation_recovery(query)")
    provider_fallback = block.index("_gold_star_remedy_selection_recovery(query)")
    assert recovery < provider_fallback
    assert "provider_invoked=false" in block
    assert "retrieval_invoked=false" in block


def test_final_visitor_boundary_repairs_provider_and_legacy_route_failures():
    start = MAIN_SOURCE.index("def _guide_finalize_visitor_payload(")
    end = MAIN_SOURCE.index("def ", start + 5)
    block = MAIN_SOURCE[start:end]
    assert "_requires_autonomy_evidence_evaluation(query)" in block
    assert "_has_autonomy_evidence_evaluation(response_text)" in block
    assert "_autonomy_evidence_evaluation_recovery(query)" in block
    assert 'safe["recommendation"] = None' in block
    assert "final_visitor_boundary_autonomy_evidence_evaluation" in block
