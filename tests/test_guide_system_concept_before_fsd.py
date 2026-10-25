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
