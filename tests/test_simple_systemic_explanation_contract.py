from simple_systemic_explanation_contract import (
    apply_simple_systemic_explanation_boundary,
    build_simple_systemic_explanation_response,
    is_simple_systemic_explanation_question,
)


def test_exact_live_question_is_recognized():
    assert is_simple_systemic_explanation_question(
        "How should The Guide explain a systemic issue to a user seeking a simple answer?"
    )


def test_close_paraphrases_are_recognized():
    queries = [
        "How can a guide describe a systemic problem in plain language for a visitor?",
        "How should I explain a structural problem simply to a reader?",
        "What is a straightforward way to communicate a system-wide issue to users?",
    ]
    assert all(is_simple_systemic_explanation_question(q) for q in queries)


def test_incidental_mentions_and_missing_intent_do_not_trigger():
    queries = [
        "What is a systemic issue?",
        "The guide is simple, but the issue is systemic.",
        "How should the Guide explain a systemic issue to a user?",
        "How should the Guide explain a simple issue to a user?",
        "What simple answer should I give about the systemic issue?",
    ]
    assert not any(is_simple_systemic_explanation_question(q) for q in queries)


def test_answer_preserves_systemic_integrity_without_overloading_user():
    answer = build_simple_systemic_explanation_response().casefold()
    for phrase in (
        "simple without making the issue simplistic",
        "conditions and relationships",
        "ordinary language",
        "known from what is inferred",
        "one cause explains everything",
        "practical",
        "deeper layers",
    ):
        assert phrase in answer


def test_final_boundary_repairs_retrieval_failure_and_separates_doorway():
    failed = "I did not identify a directly relevant Archive resource."
    result = apply_simple_systemic_explanation_boundary(
        "How should The Guide explain a systemic issue to a user seeking a simple answer?",
        {"response": failed, "answer": failed, "recommendation": None,
         "provider": "test-provider", "evidence": [{"title": "unrelated"}]},
    )
    assert result["response"] == result["answer"]
    assert "systemic issue persists" in result["response"]
    assert result["recommendation"]["title"] == "Structural Frameworks"
    assert result["canonical_doorway"] == result["recommendation"]
    assert result["answer_basis"]["kind"] == "general_knowledge"
    assert result["response_provenance"]["llm_invoked"] is True
    assert result["evidence"] == []
    assert result["simple_systemic_explanation_contract"]["answer_first_enforced"] is True


def test_nonmatching_query_is_unchanged():
    payload = {"response": "original", "recommendation": None}
    assert apply_simple_systemic_explanation_boundary(
        "What is a systemic issue?", payload
    ) is payload


def test_safety_payload_is_never_overridden():
    payload = {"intent": "SAFETY_INTERRUPT", "response": "safety response"}
    assert apply_simple_systemic_explanation_boundary(
        "How should The Guide explain a systemic issue to a user seeking a simple answer?",
        payload,
    ) is payload


def test_explicit_no_handoff_is_respected():
    result = apply_simple_systemic_explanation_boundary(
        "How should The Guide explain a systemic issue to a user seeking a simple answer? No links or resources.",
        {"response": "generic", "recommendation": {"title": "old"}},
    )
    assert result["response"]
    assert result["recommendation"] is None
    assert result["canonical_doorway"] is None
    assert result["doorway_decision"] == "omit"


def test_provenance_records_prior_provider_generation_truthfully():
    result = apply_simple_systemic_explanation_boundary(
        "How should The Guide explain a systemic issue to a user seeking a simple answer?",
        {"response": "generic", "provider": "provider-x", "model": "model-y"},
    )
    assert result["provider"] is None
    assert result["model"] is None
    assert result["response_provenance"]["llm_invoked"] is True


def test_shared_main_finalizer_integrates_architectural_boundary():
    from pathlib import Path
    source = Path(__file__).resolve().parents[1].joinpath("main.py").read_text(encoding="utf-8")
    assert "apply_simple_systemic_explanation_boundary(query, finalized)" in source
    assert source.index("apply_event_pattern_structure_boundary(query, finalized)") < source.index(
        "apply_simple_systemic_explanation_boundary(query, finalized)"
    )
