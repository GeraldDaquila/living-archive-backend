"""Regression tests for provider-independent practical recovery."""
import re

from deterministic_answer_recovery import compose_recovery


def test_first_person_how_questions_never_produce_ungrammatical_subjects():
    questions = (
        "How do I support someone without making them dependent on me?",
        "How can I help without taking away their independence?",
        "How can I tell if I am helping too much and taking over?",
    )
    for question in questions:
        answer = compose_recovery(question)
        assert answer.strip()
        assert not re.search(
            r"approach I\b|approach support someone|approach help without",
            answer,
            re.I,
        )


def test_practical_recovery_is_coherent_without_subject_interpolation():
    answer = compose_recovery(
        "How do I support someone without making them dependent on me?"
    )
    assert "A practical starting point" in answer
    assert "retain control" in answer
    assert "approach I support" not in answer
