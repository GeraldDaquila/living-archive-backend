"""Regression tests for preventing executable/template fragments in visitor answers."""

import main


def test_source_dump_detector_rejects_leaked_conditional_template():
    leaked = (
        "It sounds like you are carrying a lot. "
        "if (currentTurn === 1) { response = { reflection: '...' }; "
        "else if (currentTurn ===="
    )
    assert main._basic_inquiry_has_source_dump(leaked) is True


def test_source_dump_detector_rejects_next_question_template():
    leaked = 'nextQuestion: "When you look at this friction..."'
    assert main._basic_inquiry_has_source_dump(leaked) is True


def test_source_dump_detector_keeps_ordinary_explanation():
    answer = (
        "A problem can recur when the conditions that produce it remain unchanged. "
        "For example, a team may fix a missed handoff without assigning anyone to confirm receipt."
    )
    assert main._basic_inquiry_has_source_dump(answer) is False


def test_final_boundary_recovers_template_contamination():
    payload = {
        "ok": True,
        "response": (
            "if (currentTurn === 1) { response = { reflection: 'fragmented demands' }; "
            "else if (currentTurn ===="
        ),
        "recommendation": {"title": "Wayfinder"},
    }
    recovered = main._guide_finalize_visitor_payload(
        payload,
        "Why do the same problems keep returning even when everyone involved seems to be trying their best?",
    )
    assert "currentTurn" not in recovered["response"]
    assert "nextQuestion" not in recovered["response"]
    assert "For example" in recovered["response"]
    assert recovered["recommendation"] is None
    assert recovered["processing"] == "final_visitor_boundary_recovery"
