import event_pattern_structure_contract as contract

QUERY = "What is the difference between an event, a pattern, and a system structure?"

def test_exact_query_is_recognized():
    assert contract.is_event_pattern_structure_question(QUERY)

def test_paraphrased_distinction_is_recognized():
    assert contract.is_event_pattern_structure_question(
        "Can you distinguish events, recurring patterns, and system structures?"
    )

def test_unrelated_question_is_not_captured():
    assert not contract.is_event_pattern_structure_question("What is a system?")

def test_answer_requires_all_three_levels_and_causal_explanation():
    good = contract.event_pattern_structure_recovery()
    assert contract.has_event_pattern_structure_explanation(good)
    assert not contract.has_event_pattern_structure_explanation(
        "An event happens once. A pattern repeats. A system structure is important."
    )

def test_boundary_replaces_restatement_and_preserves_selected_doorway():
    doorway = {"title": "Fractal Systems Diagnostic", "url": "https://geralddaquila.com/fractal-systems-diagnostic-2/"}
    original = {"response": "Your question asks what the difference is. Continue exploring.", "recommendation": doorway}
    result = contract.apply_event_pattern_structure_boundary(QUERY, original)
    assert result["response"] == contract.event_pattern_structure_recovery()
    assert result["recommendation"] == doorway
    assert result["event_pattern_structure_contract"]["answer_first_enforced"] is True

def test_complete_answer_is_not_rewritten():
    answer = contract.event_pattern_structure_recovery()
    result = contract.apply_event_pattern_structure_boundary(QUERY, {"response": answer})
    assert result["response"] == answer
    assert "event_pattern_structure_contract" not in result

def test_unrelated_payload_is_unchanged():
    payload = {"response": "An unrelated answer."}
    assert contract.apply_event_pattern_structure_boundary("What is photosynthesis?", payload) is payload


def test_definition_and_relationship_paraphrases_are_recognized_without_broad_capture():
    assert contract.is_event_pattern_structure_question(
        "What are events, patterns, and system structures?"
    )
    assert contract.is_event_pattern_structure_question(
        "How do events become patterns shaped by system structures?"
    )
    assert not contract.is_event_pattern_structure_question(
        "What is a pattern in a poem?"
    )


def test_recovery_provenance_clears_unsupported_retrieval_evidence_and_preserves_doorway():
    query = "What is the difference between an event, a pattern, and a system structure?"
    doorway = {"title": "Fractal Systems Diagnostic", "url": "https://geralddaquila.com/fractal-systems-diagnostic-2/"}
    payload = {
        "response": "A restatement, not an answer.",
        "provider": "test-provider",
        "model": "test-model",
        "evidence": [{"title": "Unrelated source"}],
        "recommendation": doorway,
        "answer_envelope": {"route": {"provider_present": True, "model_present": True}, "evidence": {"references_present": True}},
    }
    result = contract.apply_event_pattern_structure_boundary(query, payload)
    assert result["response_provenance"]["class"] == "deterministic_recovery"
    assert result["response_provenance"]["provider"] == "bounded_event_pattern_structure_answer_first"
    assert result["response_provenance"]["llm_invoked"] is True
    assert result["provider"] is None and result["model"] is None
    assert result["evidence"] == []
    assert result["evidence_validation"]["status"] == "not_applicable"
    assert result["answer_envelope"]["evidence"]["references_present"] is False
    assert result["answer_envelope"]["route"]["provider_present"] is False
    assert result["recommendation"] == doorway


def test_query_specific_gold_star_doorway_is_added_from_registry_only_when_needed():
    query = "What is the difference between an event, a pattern, and a system structure?"
    result = contract.apply_event_pattern_structure_boundary(
        query,
        {"response": "A restatement, not a complete explanation."},
    )
    doorway = result["recommendation"]
    assert doorway["title"] == "Fractal Systems Diagnostic"
    assert doorway["url"] == "https://geralddaquila.com/fractal-systems-diagnostic-2/"
    assert result["canonical_doorway"] == doorway
    assert result["doorway_decision"] == "include"
    assert result["doorway_selection_source"] == "approved_query_specific_gold_star_registry_record"


def test_explicit_no_handoff_request_overrides_query_specific_doorway():
    query = (
        "What is the difference between an event, a pattern, and a system structure? "
        "Do not recommend links or resources."
    )
    result = contract.apply_event_pattern_structure_boundary(
        query,
        {"response": "A restatement, not a complete explanation."},
    )
    assert "recommendation" not in result
    assert "canonical_doorway" not in result
