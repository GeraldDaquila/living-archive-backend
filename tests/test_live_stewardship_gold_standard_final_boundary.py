from general_guide_composition import enforce_response_contracts, _requires_archive_scoped_stewardship


QUESTION = "What does stewardship mean in the Living Archive?"


def test_exact_archive_stewardship_question_is_guarded():
    assert _requires_archive_scoped_stewardship(QUESTION)


def test_old_generic_single_paragraph_is_replaced_by_gold_standard():
    old = (
        "Stewardship mean in the Living Archive is best understood by what it means "
        "and how it operates in practice. A useful definition distinguishes the idea "
        "from nearby concepts and makes its implications clear. The precise meaning "
        "can vary by field or institution, so this is a general explanation rather "
        "than a claim that the Living Archive uses a particular formal definition."
    )
    actual = enforce_response_contracts(QUESTION, old)
    assert len(actual.split("\n\n")) == 3
    assert "In the Living Archive" in actual
    assert "For example" in actual
    assert "general explanation rather than" not in actual


def test_valid_three_paragraph_archive_answer_is_preserved():
    good = (
        "In the Living Archive, stewardship means caring for knowledge and using it responsibly.\n\n"
        "For example, preserving context helps others understand what a source actually supports.\n\n"
        "Stewardship includes knowing the limits of one's responsibility and being honest about them."
    )
    assert enforce_response_contracts(QUESTION, good) == good
