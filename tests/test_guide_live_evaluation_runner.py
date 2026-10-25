from scripts.guide_live_evaluation import build_human_review_template, evaluate_gold, evaluate_held


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


def test_live_results_receive_pending_human_scorecard_not_auto_approval():
    rubric = {
        "critical_dimensions": ["answer_directness", "factual_accuracy"],
        "dimensions": [
            {"id": "answer_directness"},
            {"id": "factual_accuracy"},
            {"id": "human_voice_and_respect"},
        ],
    }
    scorecard = build_human_review_template(rubric)
    assert scorecard["status"] == "PENDING"
    assert scorecard["decision"] == "PENDING"
    assert scorecard["reviewer"] is None
    assert scorecard["reviewed_at"] is None
    assert scorecard["critical_dimensions"] == ["answer_directness", "factual_accuracy"]
    assert set(scorecard["scores"]) == {"answer_directness", "factual_accuracy", "human_voice_and_respect"}
    assert all(value is None for value in scorecard["scores"].values())
    assert "cannot approve" in scorecard["instruction"]


def test_human_scorecard_allows_case_specific_critical_dimensions():
    scorecard = build_human_review_template(
        {"critical_dimensions": ["default"], "dimensions": [{"id": "accuracy"}]},
        applicable_critical=["accuracy", "archive_grounding_and_provenance"],
    )
    assert scorecard["critical_dimensions"] == ["accuracy", "archive_grounding_and_provenance"]


def test_unspecified_doorway_url_is_not_mistaken_for_required_absence():
    record = {
        "status": "FROZEN_REFERENCE_ONLY",
        "expected_response": "Answer.",
        "expected_doorway": {"title": "Reciprocity Before Bureaucracy", "url": None},
        "assertions": ["Offer the optional doorway after the answer."],
        "freeze_policy": "Preserve the observed accepted response.",
    }
    transport = {
        "status": 200,
        "error": None,
        "body": {
            "ok": True,
            "response": "Answer.",
            "recommendation": {
                "title": "Reciprocity Before Bureaucracy",
                "url": "https://geralddaquila.com/reciprocity/",
            },
        },
    }
    checks = evaluate_gold(record, transport)
    assert all(item["passed"] for item in checks), checks
    assert not any(item["name"] == "doorway_url" for item in checks)
