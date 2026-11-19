"""WP3 calibration contract: representative held-outs, honest coverage, human review."""
import json
from pathlib import Path

from scripts.guide_live_evaluation import build_human_review_template, evaluate_held
from scripts.gold_star_paired_offline_evaluation import evaluate_dataset

ROOT = Path(__file__).resolve().parents[1]
EVALUATION_SET = ROOT / "docs/qa/guide_learning_evaluation_set.json"
PAIRED_TEMPLATE = ROOT / "docs/qa/gold_star_paired_fixture_template.json"


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_heldout_set_and_paired_template_cover_the_same_seven_case_ids():
    evaluation = _load_json(EVALUATION_SET)
    paired = _load_json(PAIRED_TEMPLATE)
    expected = {
        "heldout-water-boiling-point-001",
        "heldout-cosmology-life-001",
        "heldout-practical-trust-001",
        "heldout-strategic-governance-001",
        "heldout-technical-verification-001",
        "heldout-uncertain-causation-001",
        "heldout-explicit-no-handoff-001",
    }
    evaluation_ids = [case["case_id"] for case in evaluation["cases"]]
    paired_ids = [case["case_id"] for case in paired["cases"]]
    assert len(evaluation_ids) == len(set(evaluation_ids)) == 7
    assert len(paired_ids) == len(set(paired_ids)) == 7
    assert set(evaluation_ids) == expected
    assert set(paired_ids) == expected


def test_human_review_rubric_has_all_critical_dimensions_and_valid_scale():
    evaluation = _load_json(EVALUATION_SET)
    rubric = evaluation["human_review_rubric"]
    dimension_ids = {item["id"] for item in rubric["dimensions"]}
    assert set(rubric["critical_dimensions"]).issubset(dimension_ids)
    assert set(rubric["scale"]) == {"0", "1", "2", "NA"}
    assert "human review" in rubric["review_gate"].casefold()
    for case in evaluation["cases"]:
        assert case["split"] == "held_out"
        assert case["critical_dimensions"]
        scorecard = build_human_review_template(
            rubric, applicable_critical=case["critical_dimensions"]
        )
        assert set(case["critical_dimensions"]).issubset(scorecard["scores"])
        assert all(scorecard["scores"][key] is None for key in case["critical_dimensions"])


def test_every_heldout_question_has_a_registered_positive_evaluator_contract():
    samples = {
        "heldout-water-boiling-point-001": (
            "At standard atmospheric pressure, water boils at 100°C (212°F). "
            "The boiling point changes when atmospheric pressure changes."
        ),
        "heldout-cosmology-life-001": (
            "Cosmology is the study of the universe as a whole. A picture of reality "
            "can shape people's values, choices, and relationships. For example, "
            "a community's understanding of its place in the world can influence "
            "how it treats the natural environment."
        ),
        "heldout-practical-trust-001": (
            "Ask the people affected what they see before deciding. Explain the reasons "
            "for the decision, name who is responsible, and follow through on promises. "
            "Then check with the people affected about the result."
        ),
        "heldout-strategic-governance-001": (
            "Centralized authority can provide coordination and oversight, while "
            "distributed authority delegates local decisions to teams. However, both "
            "models have costs and risks. When decisions carry organization-wide risk, "
            "consistent direction may help; routine local decisions can be delegated. "
            "I recommend a hybrid: retain strategic safeguards centrally and delegate "
            "bounded operational authority."
        ),
        "heldout-technical-verification-001": (
            "Use os.getenv('TOKEN') is not None as a boolean presence check. Do not "
            "print or log the secret value. This confirms that configuration is present, "
            "not that the application actually reads or uses the variable at runtime."
        ),
        "heldout-uncertain-causation-001": (
            "I cannot determine the cause without analytics and referral data. Compare "
            "referral sources, UTM campaign tags, Search Console, and server logs. "
            "Segment the traffic by landing page and inspect whether the increase came "
            "from search, a campaign, referrals, or bots."
        ),
        "heldout-explicit-no-handoff-001": (
            "A policy establishes the rule or principle that guides a decision. "
            "A procedure describes the steps for carrying it out. For example, a "
            "policy may require secure handling of records, while a procedure explains "
            "how staff store and access them."
        ),
    }
    evaluation = _load_json(EVALUATION_SET)
    cases = {case["case_id"]: case for case in evaluation["cases"]}
    assert set(samples) == set(cases)
    for case_id, answer in samples.items():
        checks = evaluate_held(
            {"case_id": case_id, "query": cases[case_id]["query"]},
            {"status": 200, "error": None, "body": {
                "ok": True, "response": answer, "recommendation": None
            }},
        )
        assert checks and all(item["passed"] for item in checks), {
            "case_id": case_id, "failed_checks": [x for x in checks if not x["passed"]]
        }


def test_heldout_evaluator_fails_closed_for_unregistered_case_ids():
    checks = evaluate_held(
        {"case_id": "heldout-unregistered-999"},
        {"status": 200, "error": None, "body": {"ok": True, "response": "An answer."}},
    )
    assert any(item["name"] == "known_heldout_case" and not item["passed"] for item in checks)


def test_uncaptured_paired_outputs_remain_missing_and_are_not_counted_as_parity():
    paired = _load_json(PAIRED_TEMPLATE)
    assert all(case["llm"] is None and case["deterministic"] is None for case in paired["cases"])
    report = evaluate_dataset(paired)
    assert report["evaluation_mode"] == "offline_fixture_only"
    assert report["paired_cases"] == 0
    assert report["status_parity"] == 0
    assert report["status_disagreement"] == 0
    assert report["coverage"]["llm"]["not_applicable"] == 7
    assert report["coverage"]["deterministic"]["not_applicable"] == 7
    assert report["semantic_certification"] is False


def test_human_scorecard_is_pending_and_case_critical_dimensions_are_scoreable():
    evaluation = _load_json(EVALUATION_SET)
    rubric = evaluation["human_review_rubric"]
    scorecard = build_human_review_template(rubric)
    dimension_ids = {item["id"] for item in rubric["dimensions"]}
    assert scorecard["status"] == "PENDING"
    assert scorecard["decision"] == "PENDING"
    assert scorecard["reviewer"] is None
    assert scorecard["reviewed_at"] is None
    assert dimension_ids.issubset(scorecard["scores"])
    assert all(value is None for value in scorecard["scores"].values())
    assert set(scorecard["critical_dimensions"]) == set(rubric["critical_dimensions"])
    assert "cannot approve" in scorecard["instruction"].casefold()
    for case in evaluation["cases"]:
        case_scorecard = build_human_review_template(
            rubric, applicable_critical=case["critical_dimensions"]
        )
        assert set(case["critical_dimensions"]).issubset(case_scorecard["scores"])
        assert case_scorecard["status"] == "PENDING"
        assert case_scorecard["decision"] == "PENDING"


def test_strategic_question_echo_does_not_count_as_a_comparison_or_recommendation():
    evaluation = _load_json(EVALUATION_SET)
    case = next(
        item for item in evaluation["cases"]
        if item["case_id"] == "heldout-strategic-governance-001"
    )
    echoed_only = (
        "The question raises a real issue: "
        + case["query"].rstrip("?")
        + ". I do not have enough grounded material here to give a specific answer. "
        "A useful next question is what would change if the situation were understood differently."
    )
    checks = evaluate_held(
        {"case_id": case["case_id"], "query": case["query"]},
        {"status": 200, "error": None, "body": {
            "ok": True, "response": echoed_only, "recommendation": None
        }},
    )
    by_name = {item["name"]: item["passed"] for item in checks}
    assert by_name["compares_both_models"] is False
    assert by_name["makes_tradeoffs_visible"] is False
    assert by_name["uses_conditional_reasoning"] is False
    assert by_name["offers_reasoned_direction"] is False


def test_real_conditional_governance_analysis_still_passes_after_echo_removal():
    evaluation = _load_json(EVALUATION_SET)
    case = next(
        item for item in evaluation["cases"]
        if item["case_id"] == "heldout-strategic-governance-001"
    )
    answer = (
        "Centralized authority can provide coordination and oversight, while distributed "
        "authority delegates local decisions to teams. However, both models have costs "
        "and risks. When decisions carry organization-wide risk, consistent direction "
        "may help; routine local decisions can be delegated. I recommend a hybrid: retain "
        "strategic safeguards centrally and delegate bounded operational authority."
    )
    checks = evaluate_held(
        {"case_id": case["case_id"], "query": case["query"]},
        {"status": 200, "error": None, "body": {
            "ok": True, "response": answer, "recommendation": None
        }},
    )
    assert all(item["passed"] for item in checks), checks


def test_frozen_live_deterministic_captures_are_scored_without_question_echo_credit():
    root = Path(__file__).resolve().parents[1]
    fixture = _load_json(root / "docs/qa/gold_star_paired_fixture_template.json")
    expected_failures = {
        "heldout-water-boiling-point-001": {
            "general_fact_celsius", "general_fact_fahrenheit", "no_irrelevant_doorway"
        },
        "heldout-cosmology-life-001": {
            "defines_cosmology", "concrete_implication"
        },
        "heldout-practical-trust-001": {"concrete_actions"},
        "heldout-strategic-governance-001": {
            "compares_both_models", "makes_tradeoffs_visible",
            "uses_conditional_reasoning", "offers_reasoned_direction"
        },
        "heldout-technical-verification-001": {
            "safe_presence_check", "configuration_vs_usage"
        },
        "heldout-uncertain-causation-001": {
            "calibrates_uncertainty", "names_discriminating_evidence", "offers_investigation"
        },
        "heldout-explicit-no-handoff-001": {"explains_policy_procedure"},
    }
    for case in fixture["cases"]:
        checks = evaluate_held(
            {"case_id": case["case_id"], "query": case["query"]},
            {"status": 200, "error": None, "body": case["deterministic"]},
        )
        failed = {item["name"] for item in checks if not item["passed"]}
        assert expected_failures[case["case_id"]].issubset(failed), {
            "case_id": case["case_id"], "expected_failures": expected_failures[case["case_id"]],
            "actual_failures": failed,
        }
