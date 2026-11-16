import deterministic_answer_recovery as recovery


def test_structural_change_vs_disruption_fallback_opens_with_the_answer():
    question = "How can one distinguish structural change from ordinary disruption?"
    response = recovery.compose_recovery(question)
    opening = response.split("\n\n", 1)[0]

    assert opening == (
        "Structural change alters the underlying conditions that reproduce a pattern; "
        "ordinary disruption interrupts the pattern's visible operation without "
        "necessarily changing those conditions."
    )
    assert "The inquiry begins" not in response


def test_generic_how_recovery_does_not_use_process_announcement_opening():
    response = recovery.compose_recovery(
        "How can an organization make a consequential change responsibly?"
    )

    assert not response.startswith("The inquiry begins")
    assert response.startswith(
        "Make the intended outcome, the responsibilities involved, and the people "
        "who will live with the consequences explicit"
    )
