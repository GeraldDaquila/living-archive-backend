"""Behavioral contract tests for Gold Star Adaptive Intelligence v2.0."""
import json
from pathlib import Path

import general_guide_composition as composition


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "docs" / "qa" / "gold_standard_registry.json"


def test_v2_quality_contract_is_injected_into_actual_provider_system_message(monkeypatch):
    captured = {}

    def fake_route(**kwargs):
        captured.update(kwargs)
        return {"parsed": {"response": "Photosynthesis converts light energy into chemical energy."}}

    monkeypatch.setattr(composition, "route_with_model_bank", fake_route)
    monkeypatch.setattr(composition, "_gold_star_active_quality_contribution", lambda _q: None)
    result = composition.compose(
        use_core=object(),
        query="What is photosynthesis?",
        context_data={},
    )

    assert result is not None
    messages = captured["messages"]
    system_message = next(item["content"] for item in messages if item["role"] == "system")
    assert composition.GOLD_STAR_ADAPTIVE_INTELLIGENCE_STANDARD_VERSION == "2.0"
    for dimension in (
        "PROSE",
        "STRUCTURE",
        "COHERENCE",
        "QUESTION-FIT AND COMPETENCE",
        "DISCERNMENT AND EPISTEMIC INTEGRITY",
        "RESOLUTION AND PRACTICAL UTILITY",
        "CONTINUITY AND DEVELOPMENTAL VALUE",
        "ADAPTIVE LEARNING INTEGRITY",
    ):
        assert dimension in system_message
    assert "not as eight mandatory sections" in system_message
    assert "does not grant new benchmark authority" in system_message


def test_v2_contract_does_not_depend_on_a_gold_star_match(monkeypatch):
    captured = {}

    def fake_route(**kwargs):
        captured.update(kwargs)
        return {"parsed": {"response": "A concise answer."}}

    monkeypatch.setattr(composition, "route_with_model_bank", fake_route)
    monkeypatch.setattr(composition, "_gold_star_active_quality_contribution", lambda _q: None)
    composition.compose(use_core=object(), query="How does photosynthesis differ from cellular respiration in energy conversion?", context_data={}, integrity_recovery=True)
    system_message = next(
        item["content"] for item in captured["messages"] if item["role"] == "system"
    )
    assert "GOLD STAR ADAPTIVE INTELLIGENCE STANDARD v2.0" in system_message


def test_existing_approved_inventory_and_active_contributor_counts_are_preserved():
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    approved = [
        item for item in registry["records"]
        if item.get("status") == "USER_APPROVED_GOLD_STANDARD"
    ]
    active = [item for item in approved if item.get("runtime_transfer") is True]
    assert len(approved) == 113
    assert len(active) == 110
    assert len({item["benchmark_id"] for item in approved}) == 113


def test_v2_contract_does_not_mutate_canonical_gold_star_records():
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    approved = [
        item for item in registry["records"]
        if item.get("status") == "USER_APPROVED_GOLD_STANDARD"
    ]
    assert all(item.get("benchmark_id") for item in approved)
    assert all(item.get("provenance") for item in approved)
    assert all(item.get("freeze_policy") for item in approved)


def test_v2_heldout_suite_covers_all_required_question_classes():
    suite = json.loads(
        (ROOT / "docs" / "qa" / "guide_learning_evaluation_set.json").read_text(encoding="utf-8")
    )
    classes = {case.get("question_type") for case in suite.get("cases", [])}
    assert classes == {
        "general_fact",
        "conceptual_explanation",
        "practical_application",
        "strategic_tradeoff",
        "technical_verification",
        "uncertain_or_insufficient_evidence",
        "explicit_no_handoff",
    }
    assert len(suite["cases"]) == 7
    assert all(case.get("rubric") and case.get("critical_dimensions") for case in suite["cases"])


def test_v2_live_evaluator_has_question_specific_contracts_for_new_classes():
    from scripts.guide_live_evaluation import evaluate_held

    cases = [
        {
            "case_id": "heldout-strategic-governance-001",
            "query": "Should a growing nonprofit centralize decisions or distribute authority across its teams?",
        },
        {
            "case_id": "heldout-technical-verification-001",
            "query": "How can I verify that a Python service has a required environment variable configured without exposing its secret value?",
        },
        {
            "case_id": "heldout-uncertain-causation-001",
            "query": "What caused the sudden increase in our website traffic last week?",
        },
        {
            "case_id": "heldout-explicit-no-handoff-001",
            "query": "Explain the difference between a policy and a procedure in plain language. Do not recommend resources, links, or follow-up steps.",
        },
    ]
    expected_checks = {
        "heldout-strategic-governance-001": {
            "compares_both_models", "makes_tradeoffs_visible",
            "uses_conditional_reasoning", "offers_reasoned_direction",
        },
        "heldout-technical-verification-001": {
            "safe_presence_check", "secret_not_printed", "configuration_vs_usage",
        },
        "heldout-uncertain-causation-001": {
            "calibrates_uncertainty", "names_discriminating_evidence",
            "offers_investigation", "avoids_false_causation",
        },
        "heldout-explicit-no-handoff-001": {
            "explains_policy_procedure", "no_links_or_doorways",
            "no_unrequested_followup",
        },
    }
    for case in cases:
        result = evaluate_held(case, {"status": 200, "body": {"ok": True, "response": "Test answer."}})
        names = {item["name"] for item in result}
        assert "known_heldout_case" not in names
        assert expected_checks[case["case_id"]] <= names
