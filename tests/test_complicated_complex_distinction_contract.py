from complicated_complex_distinction_contract import (
    apply_complicated_complex_distinction_boundary,
    build_complicated_complex_response,
    is_complicated_complex_distinction_question,
)


def test_exact_live_question_is_recognized():
    assert is_complicated_complex_distinction_question(
        "What is the difference between complicated and complex?"
    )


def test_natural_language_paraphrases_are_recognized():
    queries = [
        "How do complicated and complex systems differ?",
        "Can you distinguish a complex problem from a complicated one?",
        "Complicated vs. complex: what is the distinction?",
        "What separates complexity from complication in systems?",
    ]
    assert all(is_complicated_complex_distinction_question(q) for q in queries)


def test_unrelated_co_mentions_do_not_trigger_the_contract():
    queries = [
        "I have a complicated schedule and a complex family situation.",
        "Why are complex numbers used in complicated equations?",
        "What is a complicated problem?",
        "How can a complex organization simplify its complicated processes?",
    ]
    assert not any(is_complicated_complex_distinction_question(q) for q in queries)


def test_response_explains_both_concepts_and_their_different_responses():
    answer = build_complicated_complex_response().casefold()
    for term in ("complicated system", "complex system", "feedback", "emergent",
                 "decomposition", "expertise", "adapting"):
        assert term in answer


def test_final_boundary_replaces_nonanswer_and_attaches_verified_doorway():
    payload = {
        "response": "I did not identify a directly relevant Archive resource.",
        "answer": "I did not identify a directly relevant Archive resource.",
        "recommendation": None,
        "provider": "test-provider",
        "evidence": [{"title": "unrelated"}],
    }
    result = apply_complicated_complex_distinction_boundary(
        "What is the difference between complicated and complex?", payload
    )
    assert result["response"] == result["answer"]
    assert "complicated system" in result["response"]
    assert result["recommendation"]["title"] == "Structural Frameworks"
    assert result["recommendation"]["url"] == "https://geralddaquila.com/structural-frameworks/"
    assert result["canonical_doorway"] == result["recommendation"]
    assert result["answer_basis"]["kind"] == "general_knowledge"
    assert result["response_provenance"]["llm_invoked"] is False
    assert result["evidence"] == []


def test_nonmatching_query_and_payload_are_preserved():
    payload = {"response": "original", "recommendation": None}
    result = apply_complicated_complex_distinction_boundary(
        "What makes a complex organization effective?", payload
    )
    assert result is payload


def test_safety_payload_is_never_overridden():
    payload = {"intent": "SAFETY_INTERRUPT", "response": "safety response"}
    result = apply_complicated_complex_distinction_boundary(
        "What is the difference between complicated and complex?", payload
    )
    assert result is payload
