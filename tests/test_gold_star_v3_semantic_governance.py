"""Gold Star v3 explicit semantic operating-state reporting.

These assertions verify reporting only; the v2 visitor decision is unchanged.
"""
from gold_star_response_floor import evaluate_response_floor


def test_supported_family_reports_observation_bounded_enforcement_and_no_certification():
    query = "Why do organizations repeat failures they publicly acknowledge?"
    answer = (
        "Public acknowledgment is not the same as organizational learning. "
        "Failures repeat when incentives reward the old behavior, authority is fragmented, "
        "information does not reach decision-makers, and no owner changes the process. "
        "Understanding must alter decisions, resources, accountability, and feedback. "
        "A useful test is whether the next comparable failure produces a changed response."
    )
    result = evaluate_response_floor(query, {"ok": True, "response": answer})
    states = result["semantic_governance"]

    assert result["status"] == "pass"
    assert states["diagnostic_observation"]["state"] == "available"
    assert states["diagnostic_observation"]["mode"] == "shadow_only"
    assert states["bounded_enforcement"]["state"] == "active"
    assert states["bounded_enforcement"]["status"] == "pass"
    assert states["semantic_certification"] == {
        "state": "not_certified",
        "certified": False,
        "reason": "heuristic_contracts_and_offline_calibration_do_not_establish_semantic_certification",
    }


def test_adjacent_question_reports_diagnostic_only_without_bounded_enforcement():
    query = "Why do teams sometimes resist organizational change?"
    result = evaluate_response_floor(
        query,
        {"ok": True, "response": "Teams may resist change when uncertainty and perceived costs are not addressed."},
    )
    states = result["semantic_governance"]

    assert result["status"] == "pass"
    assert states["diagnostic_observation"]["state"] == "available"
    assert states["bounded_enforcement"]["state"] == "inactive"
    assert states["bounded_enforcement"]["status"] == "not_applicable"
    assert states["semantic_certification"]["certified"] is False


def test_observer_failure_is_reported_without_claiming_certification():
    query = "Why do organizations repeat failures they publicly acknowledge?"
    result = evaluate_response_floor(query, {"ok": True, "response": "A substantive answer."})
    states = result["semantic_governance"]

    # The current observer is available in this test environment; the contract
    # still makes the non-certification boundary explicit.
    assert states["semantic_certification"]["state"] == "not_certified"
    assert states["semantic_certification"]["certified"] is False
