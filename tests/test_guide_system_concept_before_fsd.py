from general_guide_composition import _requires_systems_vs_separate_problems_explanation, _systems_vs_separate_problems_recovery

QUESTION = "What makes a situation a system rather than a collection of separate problems?"


def test_recognizes_conceptual_system_question():
    assert _requires_systems_vs_separate_problems_explanation(QUESTION)
    assert not _requires_systems_vs_separate_problems_explanation("Please diagnose why our team is stuck.")


def test_recovery_answers_concept_with_three_paragraphs():
    answer = _systems_vs_separate_problems_recovery()
    assert len([p for p in answer.split("\n\n") if p.strip()]) == 3
    for term in ("parts", "feedback", "whole", "separate problems", "FSD"):
        assert term.casefold() in answer.casefold()


def test_event_pattern_structure_is_answered_before_fsd_application():
    from event_pattern_structure_contract import (
        apply_event_pattern_structure_boundary,
        event_pattern_structure_recovery,
        has_event_pattern_structure_explanation,
    )
    query = "What is the difference between an event, a pattern, and a system structure?"
    payload = {
        "response": "Your question asks what the difference is. Continue exploring.",
        "recommendation": {
            "title": "Fractal Systems Diagnostic",
            "url": "https://geralddaquila.com/fractal-systems-diagnostic-2/",
        },
    }
    result = apply_event_pattern_structure_boundary(query, payload)
    assert has_event_pattern_structure_explanation(result["response"])
    assert result["response"] == event_pattern_structure_recovery()
    assert result["recommendation"] == payload["recommendation"]
    assert result["event_pattern_structure_contract"]["answer_first_enforced"] is True


def test_event_pattern_structure_does_not_overwrite_a_complete_answer():
    from event_pattern_structure_contract import (
        apply_event_pattern_structure_boundary,
        event_pattern_structure_recovery,
    )
    query = "What is the difference between an event, a pattern, and a system structure?"
    answer = event_pattern_structure_recovery()
    result = apply_event_pattern_structure_boundary(query, {"response": answer})
    assert result["response"] == answer
    assert "event_pattern_structure_contract" not in result


def test_live_visitor_finalizer_enforces_answer_before_fsd_and_keeps_the_doorway_separate():
    from main import _guide_finalize_visitor_payload, _resolve_exact_guide_gold_standard
    from event_pattern_structure_contract import has_event_pattern_structure_explanation

    query = "What is the difference between an event, a pattern, and a system structure?"
    assert _resolve_exact_guide_gold_standard(query) is None
    doorway = {
        "title": "Fractal Systems Diagnostic",
        "url": "https://geralddaquila.com/fractal-systems-diagnostic-2/",
    }
    result = _guide_finalize_visitor_payload(
        {
            "response": "Your question asks about three concepts. Continue to the diagnostic.",
            "recommendation": doorway,
            "provider": "test-provider",
            "model": "test-model",
        },
        query,
    )
    assert has_event_pattern_structure_explanation(result["response"])
    assert result["recommendation"] == doorway
    assert result["answer_basis"]["kind"] == "general_knowledge"
    assert result["response_provenance"]["class"] == "deterministic_recovery"
    assert result["event_pattern_structure_contract"]["answer_first_enforced"] is True
