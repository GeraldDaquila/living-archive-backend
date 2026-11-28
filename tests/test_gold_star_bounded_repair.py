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


def test_run_bounded_repair_invokes_composer_once_and_preserves_original_doorway_and_evidence():
    from gold_star_bounded_repair import run_bounded_repair

    calls = []
    payload = {
        "response": "Original deficient response.",
        "recommendation": {"title": "Verified doorway", "url": "https://geralddaquila.com/verified/"},
        "evidence": [{"id": "source-1", "title": "Source"}],
    }
    decision = {"eligible": True, "failed_criterion": "generic_nonanswer"}

    def compose_once():
        calls.append("called")
        return {
            "response": "A bounded, substantive repaired answer.",
            "provider": "controlled-provider",
            "model": "controlled-model",
            "recommendation": {"title": "Unverified replacement", "url": "https://example.org/"},
        }

    result, outcome = run_bounded_repair(
        payload, decision,
        compose_once=compose_once,
        sanitize_response=lambda value: value,
        validate_candidate=lambda candidate: {"status": "pass"},
        is_cross_question_leak=lambda value: False,
        contains_unsafe_markup=lambda value: False,
    )
    assert calls == ["called"]
    assert outcome["status"] == "repaired"
    assert outcome["attempts"] == 1
    assert result["response"] == "A bounded, substantive repaired answer."
    assert result["recommendation"] == payload["recommendation"]
    assert result["evidence"] == payload["evidence"]
    assert result["response_provenance"]["class"] == "bounded_composition_repair"


def test_failed_revalidation_keeps_original_response_and_does_not_retry():
    from gold_star_bounded_repair import run_bounded_repair

    calls = []
    payload = {"response": "Original response.", "recommendation": {"title": "Keep me"}}
    result, outcome = run_bounded_repair(
        payload, {"eligible": True, "failed_criterion": "generic_nonanswer"},
        compose_once=lambda: calls.append("called") or {"response": "Still inadequate."},
        sanitize_response=lambda value: value,
        validate_candidate=lambda candidate: {"status": "fail", "reason": "still_generic"},
        is_cross_question_leak=lambda value: False,
        contains_unsafe_markup=lambda value: False,
    )
    assert calls == ["called"]
    assert outcome["status"] == "failed"
    assert outcome["attempts"] == 1
    assert result["response"] == "Original response."
    assert result["recommendation"] == payload["recommendation"]


def test_unsafe_or_cross_question_candidate_is_rejected_after_one_attempt():
    from gold_star_bounded_repair import run_bounded_repair

    calls = []
    result, outcome = run_bounded_repair(
        {"response": "Original."},
        {"eligible": True, "failed_criterion": "generic_nonanswer"},
        compose_once=lambda: calls.append("called") or {"response": "<script>bad()</script>"},
        sanitize_response=lambda value: value,
        validate_candidate=lambda candidate: {"status": "pass"},
        is_cross_question_leak=lambda value: True,
        contains_unsafe_markup=lambda value: True,
    )
    assert calls == ["called"]
    assert outcome["status"] == "failed"
    assert outcome["attempts"] == 1
    assert result["response"] == "Original."


def test_ineligible_bounded_repair_never_invokes_composer():
    from gold_star_bounded_repair import run_bounded_repair

    calls = []
    result, outcome = run_bounded_repair(
        {"response": "Original."},
        {"eligible": False, "reason": "deterministic_only_mode"},
        compose_once=lambda: calls.append("called"),
        sanitize_response=lambda value: value,
        validate_candidate=lambda candidate: {"status": "pass"},
        is_cross_question_leak=lambda value: False,
        contains_unsafe_markup=lambda value: False,
    )
    assert calls == []
    assert outcome["status"] == "not_attempted"
    assert outcome["attempts"] == 0
    assert result["response"] == "Original."


def test_composer_exception_is_bounded_to_one_attempt_and_preserves_original():
    from gold_star_bounded_repair import run_bounded_repair

    calls = []

    def explode():
        calls.append("called")
        raise RuntimeError("controlled failure")

    result, outcome = run_bounded_repair(
        {"response": "Original."},
        {"eligible": True, "failed_criterion": "missing_answer"},
        compose_once=explode,
        sanitize_response=lambda value: value,
        validate_candidate=lambda candidate: {"status": "pass"},
        is_cross_question_leak=lambda value: False,
        contains_unsafe_markup=lambda value: False,
    )
    assert calls == ["called"]
    assert outcome["status"] == "failed"
    assert outcome["attempts"] == 1
    assert outcome["failure_type"] == "RuntimeError"
    assert result["response"] == "Original."


def test_exact_economy_life_relationship_failure_exposes_bounded_check_ids_for_repair():
    from gold_star_semantic_contract import evaluate_semantic_contract
    from gold_star_bounded_repair import repair_eligibility

    question = "What is the relationship between economy and the conditions that sustain life?"
    candidate = {
        "ok": True,
        "response": (
            "Economic activity organizes production, exchange, and distribution. "
            "It shapes communities and influences how resources are used."
        ),
    }
    semantic = evaluate_semantic_contract(question, candidate)
    assert semantic["status"] == "fail"
    assert set(semantic["failed_checks"]) == {
        "relationship_subjects_covered",
        "connecting_mechanism_explained",
        "relationship_direction_or_boundary",
    }
    floor = {
        "status": "fail",
        "reason": "supported_semantic_contract_failed",
        "semantic_enforcement": {"failed_checks": semantic["failed_checks"]},
    }
    decision = repair_eligibility(
        floor, "guide_basic_inquiry", "normal",
        True, False, 100.0, now=90.0,
    )
    assert decision["eligible"] is True
    assert decision["failed_checks"] == semantic["failed_checks"]


def test_exact_economy_life_relationship_valid_reciprocal_answer_passes_contract():
    from gold_star_semantic_contract import evaluate_semantic_contract

    question = "What is the relationship between economy and the conditions that sustain life?"
    candidate = {
        "ok": True,
        "response": (
            "The economy depends on the conditions that sustain life: healthy ecosystems, "
            "stable communities, and the capacities people need to produce and exchange "
            "what they use. The relationship is reciprocal, but not automatic; economic "
            "choices can either renew those conditions or erode them."
        ),
    }
    result = evaluate_semantic_contract(question, candidate)
    assert result["status"] == "review_required"
    assert result["failed_checks"] == []
