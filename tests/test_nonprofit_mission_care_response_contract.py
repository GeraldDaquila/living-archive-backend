from nonprofit_mission_care_response_contract import (
    evaluate_nonprofit_mission_care_response,
    is_nonprofit_mission_care_question,
    recover_nonprofit_mission_care_response,
)

QUESTION = (
    "A nonprofit is mission-driven but burning out its staff. How should the Guide "
    "connect care, structure, purpose, and operational reality?"
)
SCREENSHOT_NEARMISS = (
    "A nonprofit burns out its staff when its stated purpose outruns the structure and "
    "capacity meant to carry it. Care, structure, purpose, and operational reality are "
    "not separate programs; they are interlocking parts of one system. When they fall "
    "out of alignment, staff absorb the gap through exhaustion, turnover, and cynicism. "
    "Here is how to connect them responsibly, without treating burnout as an individual "
    "failure or a universal diagnosis that fits every team exactly the same way."
)

def test_question_family_is_narrowly_recognized():
    assert is_nonprofit_mission_care_question(QUESTION)
    assert not is_nonprofit_mission_care_question("What is the purpose of a nonprofit?")

def test_screenshot_nearmiss_is_rejected_for_missing_operational_method():
    report = evaluate_nonprofit_mission_care_response(QUESTION, SCREENSHOT_NEARMISS)
    assert report["applies"] is True
    assert report["passed"] is False
    assert "commitment_capacity_mapping" in report["missing"]
    assert "concrete_next_action" in report["missing"]

def test_deterministic_recovery_passes_all_operational_obligations():
    response = recover_nonprofit_mission_care_response()
    report = evaluate_nonprofit_mission_care_response(QUESTION, response)
    assert report["applies"] is True
    assert report["passed"] is True, report["missing"]

def test_unrelated_question_is_not_constrained():
    report = evaluate_nonprofit_mission_care_response(
        "How do community gardens improve neighborhood life?",
        "Community gardens can create shared places to grow food and build relationships.",
    )
    assert report == {"applies": False, "passed": True, "missing": []}
