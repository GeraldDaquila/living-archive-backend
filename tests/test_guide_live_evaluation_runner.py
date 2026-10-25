from scripts.guide_live_evaluation import evaluate_gold, evaluate_held


def test_exact_approved_answer_is_enforced():
    record = {
        "status": "USER_APPROVED_GOLD_STANDARD",
        "expected_response": "The approved answer.",
        "assertions": [],
        "freeze_policy": "Frozen.",
    }
    transport = {"status": 200, "error": None, "body": {"ok": True, "response": "Changed answer."}}
    checks = evaluate_gold(record, transport)
    exact = next(item for item in checks if item["name"] == "exact_answer")
    assert exact["passed"] is False


def test_explicit_no_handoff_overrides_recorded_doorway():
    record = {
        "status": "FROZEN_REFERENCE_ONLY",
        "expected_response": "One.\n\nTwo.\n\nThree.",
        "expected_doorway": {"title": "A page", "url": "https://example.org/page"},
        "assertions": ["Exactly three paragraphs.", "The explicit request not to send the visitor to another page forbids direct page handoff."],
        "freeze_policy": "Do not change expected_response.",
    }
    transport = {"status": 200, "error": None, "body": {"ok": True, "response": "One.\n\nTwo.\n\nThree.", "recommendation": None}}
    checks = evaluate_gold(record, transport)
    assert all(item["passed"] for item in checks), checks


def test_boiling_point_heldout_rejects_false_refusal():
    case = {"case_id": "heldout-water-boiling-point-001"}
    transport = {"status": 200, "error": None, "body": {"ok": True, "response": "I don't have enough verified context to answer.", "recommendation": None}}
    checks = evaluate_held(case, transport)
    assert not all(item["passed"] for item in checks)


def test_cosmology_heldout_rejects_unrelated_diagnostic_template():
    case = {"case_id": "heldout-cosmology-life-001"}
    transport = {"status": 200, "error": None, "body": {"ok": True, "response": "Separate the immediate event from the conditions that made it more likely. What detail or context would make this question most concrete?", "recommendation": None}}
    checks = evaluate_held(case, transport)
    assert not all(item["passed"] for item in checks)


def test_practical_trust_heldout_accepts_concrete_actions():
    case = {"case_id": "heldout-practical-trust-001"}
    answer = ("Ask the people affected what they see before deciding. Explain the reasons for the decision, "
              "name who is responsible for the next step, and follow through when promised. Then check with "
              "the people affected whether the action changed their experience.")
    transport = {"status": 200, "error": None, "body": {"ok": True, "response": answer, "recommendation": None}}
    checks = evaluate_held(case, transport)
    assert all(item["passed"] for item in checks), checks
