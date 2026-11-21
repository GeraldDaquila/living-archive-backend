import json
from pathlib import Path

import gold_star_lessons as lessons
from decision_rights_candidate_policy import select_policy_candidates


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = json.loads(
    (ROOT / "docs/qa/decision_rights_candidate_set_benchmark.json").read_text(encoding="utf-8")
)


def _ids(query):
    return lessons.select_lesson_candidates(query, limit=4)


def test_all_frozen_cases_follow_canonical_candidate_roles_and_conditions():
    roles = {item["benchmark_id"]: item["role"] for item in BENCHMARK["candidate_roles"]}
    for case in BENCHMARK["cases"]:
        selected = _ids(case["query"])
        actual = [item["benchmark_id"] for item in selected]
        expected = case["expected_core"] + case["expected_conditional"] + case["expected_related_conditional"]
        assert actual == expected, case["case_id"]
        assert [item.get("role") for item in selected] == [roles[item] for item in expected]
        assert all(item.get("match_basis") == "governed_decision_rights_policy" for item in selected)
        assert all(item.get("score") is None for item in selected)


def test_paraphrased_institutional_decision_rights_query_uses_core_set():
    query = "In our nonprofit, who has the actual say over a decision, and who should be answerable for its effects?"
    selected = _ids(query)
    assert {item["benchmark_id"] for item in selected} == set(
        next(case for case in BENCHMARK["cases"] if case["case_id"] == "central-question")["expected_core"]
    )
    assert all(item["role"] == "core" for item in selected)


def test_delegation_trigger_adds_only_delegated_judgment_condition():
    query = "A committee has been given discretion by the board. Does delegation make the board's responsibility disappear?"
    selected = _ids(query)
    ids = {item["benchmark_id"] for item in selected}
    assert "general-guide-delegated-judgment-moral-limits-gold-star-2026-11-13" in ids
    assert "general-guide-formal-informal-institutional-dynamics-gold-star-2026-11-18" not in ids


def test_formal_informal_trigger_adds_only_institutional_dynamics_condition():
    query = "The bylaws say members decide, but informal norms let the chair's network control the agenda. Who has power and who is accountable?"
    selected = _ids(query)
    ids = {item["benchmark_id"] for item in selected}
    assert "general-guide-formal-informal-institutional-dynamics-gold-star-2026-11-18" in ids
    assert "general-guide-delegated-judgment-moral-limits-gold-star-2026-11-13" not in ids


def test_leadership_contrast_does_not_import_decision_rights_core():
    query = "Someone has the title of director but staff follow another person's lead. How do we distinguish leadership from formal authority?"
    selected = _ids(query)
    assert len(selected) == 1
    assert selected[0]["role"] == "related_conditional"
    assert selected[0]["benchmark_id"] == "general-guide-leadership-vs-positional-authority-gold-standard-2026-10-26"


def test_ordinary_chores_and_underspecified_queries_do_not_activate_policy():
    for query in (
        "How should I assign responsibilities when organizing a home garden?",
        "How should roommates divide routine household chores fairly?",
        "Who is responsible for this?",
    ):
        assert select_policy_candidates(query, lessons._LESSONS) is None


def test_active_quality_contribution_carries_fourth_conditional_candidate():
    query = "When a board delegates a consequential decision to a committee, who remains accountable and how can the decision be challenged?"
    result = lessons.active_quality_contribution(query)
    assert result is not None
    assert len(result["candidates"]) == 4
    assert result["candidates"][-1]["role"] == "conditional"
    assert result["candidates"][-1]["activation_condition"]


def test_four_candidate_trace_and_provider_contract_are_bounded_and_complete():
    import gold_star_adjudication_trace as trace
    import gold_star_provider_adjudication as adjudication

    candidates = lessons.active_quality_contribution(
        "When a board delegates a consequential decision to a committee, who remains accountable and how can the decision be challenged?"
    )["candidates"]
    traced = trace.build_adjudication_trace({"candidates": candidates})
    assert traced["candidate_count"] == 4
    assert trace.validate_trace(traced)["valid"]
    contract = adjudication.build_adjudication_output_contract(candidates)
    for candidate in candidates:
        assert candidate["benchmark_id"] in contract
    assert len(adjudication._candidate_index(candidates)) == 4


def test_policy_fails_closed_if_a_required_core_candidate_is_missing(monkeypatch):
    policy = [item for item in lessons._LESSONS if item["id"] !=
              "general-guide-formal-actual-power-structure-gold-standard-2026-11-16"]
    result = select_policy_candidates("How do decision rights affect institutional responsibility?", policy)
    assert result == []


def test_generic_queries_preserve_the_existing_selector_path():
    query = "What is the relationship between complexity and uncertainty?"
    selected = lessons.select_lesson_candidates(query, limit=3)
    assert len(selected) <= 3
    assert all(item.get("match_basis") != "governed_decision_rights_policy" for item in selected)

def test_provider_adjudication_validates_four_candidate_dispositions_and_spans():
    import gold_star_provider_adjudication as adjudication

    candidates = lessons.active_quality_contribution(
        "When a board delegates a consequential decision to a committee, who remains accountable and how can the decision be challenged?"
    )["candidates"]
    spans = [
        "Decision mandates define who can decide.",
        "Actual influence reveals who shapes outcomes.",
        "Accountability follows influence and capacity.",
        "Delegation preserves oversight and correction duties.",
    ]
    response = " ".join(spans)
    report = {
        "candidate_assessments": [
            {"candidate_id": item["benchmark_id"], "decision": "select", "reason_code": None}
            for item in candidates
        ],
        "application_evidence_spans": [
            {"candidate_id": item["benchmark_id"], "span": span}
            for item, span in zip(candidates, spans)
        ],
    }
    normalized = adjudication.normalize_provider_adjudication(
        report, response=response, candidates=candidates
    )
    assert normalized["status"] == "provider_reported_selected"
    assert len(normalized["selected_candidate_ids"]) == 4
    assert normalized["application_evidence_present"] is True
    assert len(normalized["application_evidence_candidate_ids"]) == 4


def test_shadow_observation_handles_policy_candidate_without_similarity_score():
    benchmark_id, score = lessons.shadow_observation(
        "How do decision rights affect institutional responsibility?"
    )
    assert benchmark_id == "general-guide-actionable-ethical-responsibility-gold-standard-2026-11-15"
    assert score is None
