"""Final-payload regressions for reflective deterministic recovery."""

import main


def test_completed_reflective_recovery_rejects_appended_generic_composition():
    question = "How can hope be disciplined rather than naïve?"
    expected = main._sanitize_basic_inquiry_response(
        main._compose_provider_exhaustion_recovery(question)
    )
    contaminated = expected + "\n\nA useful way to examine this is: acknowledge genuine openness before answering."

    actual = main._enforce_reflective_recovery_completion(question, contaminated)

    assert actual == expected
    assert "A useful way to examine this is" not in actual


def test_reflective_final_boundary_preserves_nonmatching_provider_answer():
    question = "How can hope be disciplined rather than naïve?"
    provider_answer = "A distinct provider answer with its own explanatory structure."

    assert main._enforce_reflective_recovery_completion(question, provider_answer) == provider_answer


def test_reflective_final_boundary_does_not_capture_practical_questions():
    question = "How can an organization make a consequential change responsibly?"
    response = "A practical answer with a separate structure."

    assert main._enforce_reflective_recovery_completion(question, response) == response
