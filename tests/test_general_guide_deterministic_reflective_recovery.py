"""Regression tests for reflective-conceptual deterministic recovery."""

import deterministic_answer_recovery as recovery


def test_hope_question_does_not_fall_through_to_generic_decision_template():
    question = "How can hope be disciplined rather than naïve?"
    answer = recovery.compose_recovery(question)
    paragraphs = answer.split("\n\n")

    assert len(paragraphs) == 3
    assert paragraphs[0].startswith("Hope can be disciplined without becoming naïve")
    assert "Start by defining the outcome" not in answer
    assert "responsibilities that cannot be lost" not in answer
    assert all(term in answer.casefold() for term in ("hope", "naïve", "uncertainty"))


def test_reflective_conceptual_recovery_generalizes_beyond_hope():
    question = "How can conviction remain firm without becoming rigid?"
    answer = recovery.compose_recovery(question)

    assert answer.startswith("Conviction can remain firm without becoming rigid")
    assert len(answer.split("\n\n")) == 3
    assert "Start by defining the outcome" not in answer


def test_explicit_practical_how_question_keeps_practical_recovery():
    question = "How can an organization make a consequential change responsibly?"
    answer = recovery.compose_recovery(question)

    assert answer.startswith("Start by defining the outcome")
    assert "compare realistic options" in answer

def test_generic_why_recovery_does_not_repeat_the_question_frame():
    question = "Why can a well-designed policy still fail during implementation?"
    answer = recovery.compose_recovery(question)

    assert answer.startswith("A useful explanation begins by distinguishing the immediate event")
    assert "why Why" not in answer
    assert "well-designed policy" not in answer or answer.count("well-designed policy") <= 1
    assert len(answer.split(chr(10) + chr(10))) == 3
