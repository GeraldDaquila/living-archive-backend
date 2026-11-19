"""Bounded repair eligibility tests."""
from gold_star_bounded_repair import repair_eligibility


def _floor(reason):
    return {"status": "fail", "reason": reason}


def test_one_repair_is_allowed_only_for_observable_composition_defects():
    result = repair_eligibility(
        _floor("generic_nonanswer"), "guide_basic_inquiry", "normal",
        True, False, 100.0, now=90.0,
    )
    assert result["eligible"] is True
    assert result["max_attempts"] == 1


def test_evidence_provenance_failures_are_not_repaired_by_rewording():
    result = repair_eligibility(
        _floor("archive_claim_without_verified_evidence"), "guide_basic_inquiry",
        "normal", True, False, 100.0, now=90.0,
    )
    assert result["eligible"] is False
    assert result["reason"] == "defect_not_safely_repairable"


def test_deterministic_exact_and_already_repaired_routes_never_retry():
    assert not repair_eligibility(_floor("generic_nonanswer"), "guide_early_deterministic_boundary", "normal", True, False, 100.0, now=90.0)["eligible"]
    assert not repair_eligibility(_floor("generic_nonanswer"), "guide_basic_inquiry", "deterministic_only", True, False, 100.0, now=90.0)["eligible"]
    assert not repair_eligibility(_floor("generic_nonanswer"), "guide_basic_inquiry", "normal", True, False, 100.0, exact_standard=True, now=90.0)["eligible"]
    assert not repair_eligibility(_floor("generic_nonanswer"), "guide_basic_inquiry", "normal", True, True, 100.0, now=90.0)["eligible"]


def test_repair_requires_one_shared_deadline_reserve_and_available_composer():
    assert not repair_eligibility(_floor("missing_answer"), "guide_basic_inquiry", "normal", True, False, 100.0, now=96.0)["eligible"]
    assert not repair_eligibility(_floor("missing_answer"), "guide_basic_inquiry", "normal", False, False, 100.0, now=90.0)["eligible"]
