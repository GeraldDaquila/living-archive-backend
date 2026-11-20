import json
from pathlib import Path

from deterministic_answer_recovery import compose_task_specific_recovery

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "qa" / "gold_standard_registry.json"
QUERY = "What kinds of boundaries should be drawn around a problem, and what do they exclude?"


def test_problem_boundary_question_has_provider_independent_answer_and_verified_doorway():
    result = compose_task_specific_recovery(QUERY)
    assert result is not None
    assert result["recovery_id"] == "task_problem_boundary_calibration"
    answer = result["response"]
    for concept in (
        "phenomenon", "system", "scale and place", "time horizon",
        "stakeholder and authority boundary", "evidence boundary",
        "outside the chosen scope", "materially change the diagnosis",
        "revise it",
    ):
        assert concept.casefold() in answer.casefold()
    assert result["recommendation"]["title"] == "Boundary Conditions"
    assert result["recommendation"]["url"] == "https://geralddaquila.com/boundary-conditions/"


def test_problem_boundary_recovery_handles_close_paraphrases_but_not_unrelated_questions():
    for query in (
        "How should I define the boundaries around a system problem, and what stays outside scope?",
        "When framing a problem, what should be included and excluded?",
    ):
        result = compose_task_specific_recovery(query)
        assert result is not None
        assert result["recovery_id"] == "task_problem_boundary_calibration"
    assert compose_task_specific_recovery("What boundaries should I set in a personal relationship?") is None


def test_problem_boundary_candidate_is_pending_user_review_and_not_active_learning():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "gs-2026-11-20-problem-boundary-calibration"
    )
    assert record["status"] == "CANDIDATE_PENDING_USER_REVIEW"
    assert record["explicit_user_elevation_approval"] is True
    assert record["user_reviewed_response"] is False
    assert record["runtime_transfer"] is False
    assert record["gold_star_capabilities"]["active_quality_contributor"] is False
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert record["expected_doorway"]["title"] == "Boundary Conditions"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/boundary-conditions/"
    assert len(record["expected_response"].split("\n\n")) == 3


def test_main_early_task_route_preserves_a_verified_recovery_doorway():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert '"recommendation": _normalize_authoritative_recommendation(_task_recovery.get("recommendation") or _task_recovery.get("canonical_doorway"))' in source
    assert '"doorway_url": str((_task_recovery.get("recommendation") or _task_recovery.get("canonical_doorway") or {}).get("url") or _task_recovery.get("doorway_url") or "") or None' in source
