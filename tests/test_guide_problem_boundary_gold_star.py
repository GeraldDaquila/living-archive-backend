import json
from pathlib import Path

from deterministic_answer_recovery import compose_task_specific_recovery
from main import _guide_restore_verified_doorway, _normalize_authoritative_recommendation

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
    assert _normalize_authoritative_recommendation(result["recommendation"])["title"] == "Boundary Conditions"


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
    assert record["known_theme"]
    assert registry["integrity_audit"]["registry_record_count"] == len(registry["records"])
    assert registry["audit"]["registry_record_count"] == len(registry["records"])
    assert registry["integrity_audit"]["structural_candidates_pending_live_review"] == 2
    assert len(record["expected_response"].split("\n\n")) == 3


def test_main_early_task_route_preserves_a_verified_recovery_doorway():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert '"recommendation": _task_doorway' in source
    assert '"doorway_url": _task_doorway.get("url") if _task_doorway else None' in source
    assert '"doorway_selection_source": "registered_task_recovery" if _task_doorway else "no_verified_task_doorway"' in source
    assert "trusted_task_selection" in source
    fallback_start = source.index("def _guide_route_fallback")
    fallback_task = source.index("_compose_task_specific_recovery(query) is not None", fallback_start)
    fallback_fsd = source.index("if _is_fsd_request(query)", fallback_start)
    assert fallback_task < fallback_fsd
    asgi_task = source.index("_early_task_recovery = (")
    asgi_fsd = source.index("# Immediate FSD handoff", asgi_task)
    assert asgi_task < asgi_fsd
    assert "task_recovery=task_recovery" in source


def test_shared_final_visitor_boundary_preserves_a_verified_task_recovery_doorway():
    recovery = compose_task_specific_recovery(QUERY)
    doorway = _normalize_authoritative_recommendation(recovery["recommendation"])
    payload = {
        "query": QUERY,
        "response": recovery["response"],
        "recommendation": doorway,
        "canonical_doorway": doorway,
        "doorway_title": doorway["title"],
        "doorway_url": doorway["url"],
        "doorway_rationale": doorway["rationale"],
        "doorway_selection_source": "registered_task_recovery",
        "doorway_selection_evaluated": True,
        "route_source": "guide_early_deterministic_boundary",
        "response_provenance": {"class": "deterministic_recovery"},
    }
    result = _guide_restore_verified_doorway(payload, QUERY)
    assert result["recommendation"]["title"] == "Boundary Conditions"
    assert result["recommendation"]["url"] == "https://geralddaquila.com/boundary-conditions/"
    assert result["doorway_decision"] == "selected"
    assert result["doorway_selection_source"] == "registered_task_recovery"
