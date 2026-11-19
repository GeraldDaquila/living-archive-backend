import pytest

import main
from deterministic_answer_recovery import compose_task_specific_recovery


CASES = [
    (
        "Explain the difference between a policy and a procedure in plain language. Do not recommend resources, links, or follow-up steps.",
        "task_comparison_policy_procedure",
        ("policy sets direction", "procedure explains the method"),
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
