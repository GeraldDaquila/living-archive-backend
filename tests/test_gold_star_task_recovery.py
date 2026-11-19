import pytest

import main
from deterministic_answer_recovery import compose_task_specific_recovery
from gold_star_semantic_contract import evaluate_semantic_contract


CASES = [
    (
        "Explain the difference between a policy and a procedure in plain language. Do not recommend resources, links, or follow-up steps.",
        "task_comparison_policy_procedure",
        ("policy sets direction", "procedure explains the method"),
    ),
    (
        "How can an organization put trust into practice?",
        "task_practical_trust_in_organizations",
        ("ask those affected", "explain the reasons", "follow through", "check whether trust is actually improving"),
    ),
    (
        "Should a growing nonprofit centralize decisions or distribute authority across its teams?",
        "task_decision_rights_distribution_tradeoff",
        ("centralization", "distributed authority", "hybrid"),
    ),
    (
        "How can I verify that a Python service has a required environment variable configured without exposing its secret value?",
        "task_safe_environment_variable_presence_check",
        ("os.getenv", "configured", "does not prove that the application reads"),
    ),
    (
        "What caused the sudden increase in our website traffic last week?",
        "task_uncertain_website_traffic_causation",
        ("cannot be established", "segment", "cause as undetermined"),
    ),
    (
        "How do assumptions about reality shape the way people make everyday decisions and cooperate with others?",
        "task_worldview_everyday_decisions_and_cooperation",
        ("worldview", "for example", "cooperation"),
    ),
]


@pytest.mark.parametrize("question,recovery_id,required", CASES)
def test_task_specific_recovery_is_complete_and_question_fit(question, recovery_id, required):
    result = compose_task_specific_recovery(question)

    assert result is not None
    assert result["recovery_id"] == recovery_id
    answer = result["response"].casefold()
    for phrase in required:
        assert phrase.casefold() in answer
    semantic = evaluate_semantic_contract(question, {
        "ok": True,
        "response": result["response"],
        "recommendation": None,
    })
    assert semantic["status"] != "fail"
    assert not semantic.get("hard_failures")


@pytest.mark.parametrize("question,recovery_id,_required", CASES)
def test_basic_inquiry_consumes_task_recovery_before_retrieval(
    monkeypatch, question, recovery_id, _required
):
    monkeypatch.setattr(main, "_gold_star_shadow_observation", None)
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda _query: None)
    monkeypatch.setattr(
        main.general_guide_composition,
        "_gold_star_remedy_selection_recovery",
        lambda _query: None,
    )
    monkeypatch.setattr(
        main.general_guide_composition,
        "clarification_response",
        lambda _query, _history: None,
    )

    def retrieval_must_not_run(*_args, **_kwargs):
        raise AssertionError("Task-capable deterministic recovery must precede retrieval.")

    monkeypatch.setattr(main.use_core, "fetch_canonical_context", retrieval_must_not_run)

    result = main._basic_inquiry_response(query=question, history=[], raw_body={})

    assert result["ok"] is True
    assert result["recovery"] == recovery_id
    assert result["response_provenance"]["class"] == "deterministic_recovery"
    assert result["response_provenance"]["llm_invoked"] is False
    assert result["recommendation"] is None


def test_explicit_no_handoff_detects_resource_and_followup_prohibitions():
    question = (
        "Explain the difference between a policy and a procedure in plain language. "
        "Do not recommend resources, links, or follow-up steps."
    )
    assert main._guide_query_explicitly_forbids_handoff(question)


def test_final_visitor_boundary_removes_unrequested_resource_and_followup_prose():
    question = (
        "Explain the difference between a policy and a procedure in plain language. "
        "Do not recommend resources, links, or follow-up steps."
    )
    payload = {
        "ok": True,
        "intent": "TOPICAL_INQUIRY",
        "query": question,
        "response": (
            "A policy states the rule that guides a decision, while a procedure gives the steps for carrying it out.\n\n"
            "The Archive material available here offers a place to explore further. "
            "Where would this make the biggest difference right now?"
        ),
        "recommendation": {"title": "Analytical Procedure", "url": "https://example.org/procedure"},
        "canonical_doorway": {"title": "Analytical Procedure", "url": "https://example.org/procedure"},
    }

    result = main._guide_finalize_visitor_payload(payload, question)

    assert result["recommendation"] is None
    assert result["canonical_doorway"] is None
    assert "Archive material" not in result["response"]
    assert "explore further" not in result["response"]
    assert "Where would" not in result["response"]
    assert "policy states the rule" in result["response"]


def test_water_boiling_point_uses_a_query_matched_registered_fact():
    question = "At standard atmospheric pressure, what temperature does water boil at?"
    result = main._established_general_knowledge_recovery(question)

    assert result["fact_id"] == "water_boiling_point_sea_level"
    assert "100°C" in result["response"]
    assert "212°F" in result["response"]


def test_registered_fact_is_preserved_only_for_its_own_query_at_final_integrity_gate():
    question = "At standard atmospheric pressure, what temperature does water boil at?"
    recovery = main._established_general_knowledge_recovery(question)

    assert main._guide_registered_fact_matches_current_response(
        question, recovery["response"], recovery
    )
    assert not main._guide_registered_fact_matches_current_response(
        question,
        "A different approved answer that does not answer the boiling-point question.",
        recovery,
    )
