"""Tests for consent-gated recurring-pattern detection and non-automatic elevation."""
import pytest

from gold_star_pattern_detection import (
    adjudicate_pattern_candidate,
    detect_recurring_patterns,
)


def _evidence(case, domain, task, ref=None):
    return {
        "case_id": f"case-{case}",
        "evidence_ref": ref or f"review:{case}:sha256",
        "consent_status": "CONSENTED",
        "deidentified": True,
        "human_review_status": "COMPLETE",
        "review_outcome": "CONFIRMED_DEFECT",
        "task_family": task,
        "domain": domain,
        "reasoning_operation": "answer_before_navigation",
        "failed_criterion": "answer_directness",
    }


def _qualifying_set():
    return [
        _evidence("1", "governance", "strategic"),
        _evidence("2", "education", "explanatory"),
        _evidence("3", "community", "practical"),
    ]


def test_recurring_pattern_requires_distinct_consented_reviewed_cases_across_domains_and_tasks():
    result = detect_recurring_patterns(_qualifying_set())
    assert len(result["candidates"]) == 1
    candidate = result["candidates"][0]
    assert candidate["support_count"] == 3
    assert len(candidate["domain_coverage"]) == 3
    assert len(candidate["task_family_coverage"]) == 3
    assert candidate["status"] == "CANDIDATE_REQUIRES_HUMAN_ADJUDICATION"
    assert candidate["runtime_eligible"] is False
    assert candidate["lesson_text"] is None
    assert result["runtime_activation"] is False


def test_same_domain_or_same_task_only_does_not_generalize_across_questions():
    same_domain = [
        _evidence("1", "governance", "strategic"),
        _evidence("2", "governance", "explanatory"),
        _evidence("3", "governance", "practical"),
    ]
    same_task = [
        _evidence("1", "governance", "strategic"),
        _evidence("2", "education", "strategic"),
        _evidence("3", "community", "strategic"),
    ]
    assert detect_recurring_patterns(same_domain)["candidates"] == []
    assert detect_recurring_patterns(same_task)["candidates"] == []


def test_unconsented_unreviewed_or_non_deidentified_observations_are_excluded():
    records = _qualifying_set()
    records[0]["consent_status"] = "UNKNOWN"
    records[1]["human_review_status"] = "PENDING"
    records[2]["deidentified"] = False
    result = detect_recurring_patterns(records)
    assert result["candidates"] == []
    assert result["excluded_observations"] == 3


def test_raw_question_answer_and_identity_fields_are_rejected():
    records = _qualifying_set()
    records[0]["query"] = "raw visitor query"
    records[1]["answer"] = "raw answer"
    records[2]["user_id"] = "private-id"
    result = detect_recurring_patterns(records)
    assert result["candidates"] == []
    assert result["excluded_observations"] == 3


def test_duplicate_cases_and_duplicate_evidence_cannot_manufacture_support():
    records = _qualifying_set()
    records[2]["case_id"] = records[1]["case_id"]
    records[2]["evidence_ref"] = records[1]["evidence_ref"]
    result = detect_recurring_patterns(records)
    assert result["candidates"] == []
    assert result["excluded_observations"] == 1


def test_detection_thresholds_cannot_be_weakened_below_governed_minimum():
    with pytest.raises(ValueError):
        detect_recurring_patterns(_qualifying_set(), min_support=2)
    with pytest.raises(ValueError):
        detect_recurring_patterns(_qualifying_set(), min_domains=1)
    with pytest.raises(ValueError):
        detect_recurring_patterns(_qualifying_set(), min_task_families=1)


def test_candidate_cannot_become_runtime_active_without_all_tests_and_explicit_owner_approval():
    candidate = detect_recurring_patterns(_qualifying_set())["candidates"][0]
    blocked = adjudicate_pattern_candidate(
        candidate,
        decision="APPROVE",
        reviewer="stewardship reviewer",
        rationale="The structural operation is supported by reviewed evidence.",
        target_tests_passed=True,
        adjacent_tests_passed=True,
        unrelated_negative_controls_passed=True,
        explicit_owner_approval=False,
    )
    assert blocked["status"] == "APPROVAL_BLOCKED"
    assert blocked["registry_write_performed"] is False
    assert blocked["runtime_activated"] is False


def test_approved_candidate_still_requires_separate_registry_review_and_never_activates():
    candidate = detect_recurring_patterns(_qualifying_set())["candidates"][0]
    approved = adjudicate_pattern_candidate(
        candidate,
        decision="APPROVE",
        reviewer="authorized reviewer",
        rationale="Target, adjacent, and unrelated negative controls pass.",
        target_tests_passed=True,
        adjacent_tests_passed=True,
        unrelated_negative_controls_passed=True,
        explicit_owner_approval=True,
    )
    assert approved["status"] == "APPROVED_FOR_SEPARATE_REGISTRY_REVIEW_ONLY"
    assert approved["registry_write_performed"] is False
    assert approved["runtime_activated"] is False
    assert approved["next_step"].startswith("separate_registry_change")


def test_revision_and_rejection_are_non_mutating():
    candidate = detect_recurring_patterns(_qualifying_set())["candidates"][0]
    for decision, expected in [("REVISE", "REVISION_REQUIRED"), ("REJECT", "REJECTED")]:
        result = adjudicate_pattern_candidate(
            candidate,
            decision=decision,
            reviewer="reviewer",
            rationale="Evidence does not justify current promotion.",
            target_tests_passed=False,
            adjacent_tests_passed=False,
            unrelated_negative_controls_passed=False,
        )
        assert result["status"] == expected
        assert result["registry_write_performed"] is False
        assert result["runtime_activated"] is False
