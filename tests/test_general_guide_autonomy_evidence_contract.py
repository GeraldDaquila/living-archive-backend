"""Regression tests for task-specific evaluation of Guide capability claims."""

import general_guide_composition as guide


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
