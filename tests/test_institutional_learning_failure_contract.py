from institutional_learning_failure_contract import (
    apply_institutional_learning_failure_boundary,
    build_institutional_learning_failure_response,
    institutional_learning_failure_response_checks,
    institutional_learning_failure_response_meets_contract,
    is_institutional_learning_failure_question,
)


LIVE_QUESTION = "Why do organizations repeat failures they publicly acknowledge?"


def test_exact_live_question_and_natural_paraphrases_match():
    queries = [
        LIVE_QUESTION,
        "Why do institutions keep repeating mistakes they have already admitted?",
        "How come organizations reproduce the same problems after publicly recognizing them?",
        "Why are acknowledged institutional failures still recurring?",
        "What explains companies continuing to make the same errors after reporting them?",
    ]
    assert all(is_institutional_learning_failure_question(q) for q in queries)


def test_adjacent_questions_do_not_trigger_the_bounded_recovery():
    queries = [
        "What is institutional learning?",
        "How can an organization improve its feedback process?",
        "Why do organizations fail?",
        "What are common organizational problems?",
        "Why do organizations repeat a successful process?",
        "How can a team learn from mistakes?",
    ]
    assert not any(is_institutional_learning_failure_question(q) for q in queries)


def test_gold_star_question_contract_resolves_the_causal_task_and_evidence_boundary():
    from gold_star_question_contract import build_question_contract

    contract = build_question_contract(LIVE_QUESTION)
    assert contract["task"]["primary"] == "institutional_learning_failure_candidate"
    assert contract["domain"] == {
        "primary": "organizational_systems",
        "subdomain": "institutional_learning_and_correctability",
    }
    assert contract["requested_outcome"] == "explain_why_acknowledged_institutional_failures_recur"
    assert contract["reasoning_mode"] == "causal_systems_explanation"
    assert contract["evidence"]["provenance_required"] is False
    assert "connect_understanding_to_changed_action" in contract["response"]["completion_criteria"]


def test_semantic_contract_classifies_family_and_rejects_nonanswers():
    from gold_star_semantic_contract import classify_question, evaluate_semantic_contract

    assert classify_question(LIVE_QUESTION)["type"] == "institutional_learning_failure"
    weak = "Your question asks why organizations repeat failures they publicly acknowledge."
    rejected = evaluate_semantic_contract(LIVE_QUESTION, {"ok": True, "response": weak})
    assert rejected["status"] == "fail"
    assert rejected["hard_failures"]

    good = build_institutional_learning_failure_response()
    accepted = evaluate_semantic_contract(LIVE_QUESTION, {"ok": True, "response": good})
    assert accepted["status"] == "review_required"
    assert all(check["passed"] for check in accepted["checks"])


def test_v2_floor_enforces_only_the_bounded_supported_semantic_family():
    from gold_star_response_floor import evaluate_response_floor, apply_response_floor_boundary

    weak = "Your question asks why organizations repeat failures they publicly acknowledge."
    rejected = evaluate_response_floor(
        LIVE_QUESTION,
        {"ok": True, "query": LIVE_QUESTION, "response": weak},
    )
    assert rejected["status"] == "fail"
    assert rejected["reason"] == "supported_semantic_contract_failed"
    assert rejected["semantic_enforcement"]["enforced"] is True

    recovered = build_institutional_learning_failure_response()
    accepted = evaluate_response_floor(
        LIVE_QUESTION,
        {"ok": True, "query": LIVE_QUESTION, "response": recovered},
    )
    assert accepted["status"] == "pass"
    assert accepted["semantic_enforcement"]["status"] == "pass"

    unrelated = evaluate_response_floor(
        "Tell me something interesting.",
        {"ok": True, "query": "Tell me something interesting.", "response": "Here is a short observation."},
    )
    assert unrelated["status"] == "pass"
    assert unrelated["semantic_enforcement"]["enforced"] is False


def test_v2_floor_fails_closed_when_supported_semantic_observer_is_unavailable(monkeypatch):
    import gold_star_response_floor as floor

    monkeypatch.setattr(
        floor,
        "_semantic_shadow",
        lambda query, payload: {
            "version": "1.0",
            "mode": "shadow_only",
            "status": "observer_error",
            "reason": "test_observer_failure",
            "question_type": "unknown",
            "enforced": False,
        },
    )
    result = floor.evaluate_response_floor(
        LIVE_QUESTION,
        {
            "ok": True,
            "query": LIVE_QUESTION,
            "response": build_institutional_learning_failure_response(),
        },
    )
    assert result["status"] == "fail"
    assert result["reason"] == "supported_semantic_contract_failed"
    assert result["semantic_enforcement"]["enforced"] is True


def test_v2_floor_preserves_frozen_exact_gold_standard_immutability():
    from gold_star_response_floor import evaluate_response_floor

    weak = "Your question asks why organizations repeat failures they publicly acknowledge."
    result = evaluate_response_floor(
        LIVE_QUESTION,
        {"ok": True, "query": LIVE_QUESTION, "response": weak},
        exact_standard=True,
    )
    assert result["status"] == "pass"
    assert result["semantic_enforcement"]["reason"] == "exact_gold_standard_immutable"


def test_v2_sender_fails_closed_if_supported_semantic_recovery_is_bypassed():
    from gold_star_response_floor import apply_response_floor_boundary

    weak = "Your question asks why organizations repeat failures they publicly acknowledge."
    payload, status = apply_response_floor_boundary(
        LIVE_QUESTION,
        {"ok": True, "query": LIVE_QUESTION, "response": weak},
        200,
    )
    assert status == 503
    assert payload["error_type"] == "gold_star_v2_quality_floor_rejected"
    assert payload["gold_star_v2_quality_floor"]["reason"] == "supported_semantic_contract_failed"


def test_recovery_answer_meets_every_substantive_requirement():
    answer = build_institutional_learning_failure_response()
    assert institutional_learning_failure_response_meets_contract(answer)
    assert all(check["passed"] for check in institutional_learning_failure_response_checks(answer))
    for phrase in (
        "acknowledging a failure",
        "incentives",
        "authority",
        "institutional memory",
        "understanding",
        "what it does",
        "Who owns the correction?",
        "not a diagnosis of every organization",
    ):
        assert phrase.casefold() in answer.casefold()


def test_generic_question_echo_is_replaced_with_a_substantive_first_answer_and_doorway():
    failed = (
        "Your question asks why organizations repeat failures they publicly acknowledge. "
        "That gives you a starting point; the separately selected Archive resource offers a place to explore further."
    )
    result = apply_institutional_learning_failure_boundary(
        LIVE_QUESTION,
        {"response": failed, "recommendation": None, "provider": "provider-x", "model": "model-y"},
    )
    assert result["institutional_learning_failure_contract"]["recovery_applied"] is True
    if "answer" in result:
        assert result["response"] == result["answer"]
    assert "Because acknowledging a failure" in result["response"]
    assert result["recommendation"]["title"] == "When Experience Can Change Us: The Two Capacities of a Living System"
    assert result["canonical_doorway"] == result["recommendation"]
    assert result["doorway_url"].endswith("/when-experience-can-change-us-the-two-capacities-of-a-living-system/")
    assert result["answer_basis"]["kind"] == "general_knowledge"
    assert result["evidence"] == []
    assert result["response_provenance"]["llm_invoked"] is True


def test_substantive_answer_is_preserved_but_verified_doorway_is_restored():
    answer = build_institutional_learning_failure_response()
    result = apply_institutional_learning_failure_boundary(
        LIVE_QUESTION,
        {"response": answer, "recommendation": None},
    )
    assert result["response"] == answer
    assert result["institutional_learning_failure_contract"]["recovery_applied"] is False
    assert result["doorway_decision"] == "include"


def test_explicit_no_handoff_is_respected_even_during_recovery():
    result = apply_institutional_learning_failure_boundary(
        LIVE_QUESTION + " No links or resources.",
        {"response": "Your question asks about organizations.", "recommendation": {"title": "Old"}},
    )
    assert result["institutional_learning_failure_contract"]["recovery_applied"] is True
    assert result["recommendation"] is None
    assert result["canonical_doorway"] is None
    assert result["doorway_decision"] == "omit"


def test_safety_routes_are_never_overridden():
    payload = {"intent": "SAFETY_INTERRUPT", "response": "safety response"}
    assert apply_institutional_learning_failure_boundary(LIVE_QUESTION, payload) is payload


def test_nonmatching_queries_are_unchanged():
    payload = {"response": "original"}
    assert apply_institutional_learning_failure_boundary("What is institutional learning?", payload) is payload


def test_shared_finalizer_invokes_contract_after_inner_routes_and_preserves_exact_standards():
    from pathlib import Path
    source = Path(__file__).resolve().parents[1].joinpath("main.py").read_text(encoding="utf-8")
    assert "apply_institutional_learning_failure_boundary(query, finalized)" in source
    assert source.index("if _resolve_exact_guide_gold_standard(query) is not None:") < source.index(
        "apply_institutional_learning_failure_boundary(query, finalized)"
    )
    assert source.index("apply_institutional_learning_failure_boundary(query, finalized)") < source.index(
        "return finalized", source.index("apply_institutional_learning_failure_boundary(query, finalized)")
    )
