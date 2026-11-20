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
