from general_guide_composition import enforce_response_contracts, _requires_archive_scoped_stewardship


QUESTION = "What does stewardship mean in the Living Archive?"


def test_archive_scoped_stewardship_requires_three_real_paragraphs():
    assert _requires_archive_scoped_stewardship(QUESTION)
    old = (
        "Stewardship mean in the Living Archive is best understood by what it means "
        "and how it operates in practice. A useful definition distinguishes the idea "
        "from nearby concepts and makes its implications clear. The precise meaning "
        "can vary by field or institution, so this is a general explanation rather "
        "than a claim that the Living Archive uses a particular formal definition."
    )
    result = enforce_response_contracts(QUESTION, old)
    paragraphs = [p.strip() for p in result.split("\n\n") if p.strip()]
    assert len(paragraphs) == 3
    assert paragraphs[0].startswith("In the Living Archive, stewardship")
    assert "For example" in paragraphs[1]
    assert "general explanation rather than" not in result


def test_valid_three_paragraph_archive_answer_is_preserved():
    valid = (
        "In the Living Archive, stewardship follows understanding and means caring "
        "for knowledge and using it responsibly.\n\n"
        "For example, preserving source context helps readers distinguish what a "
        "source says from an interpretation.\n\n"
        "Stewardship includes acting within one's responsibilities and being honest "
        "about what remains uncertain."
    )
    assert enforce_response_contracts(QUESTION, valid) == valid


def test_general_stewardship_question_is_not_forced_into_archive_specific_recovery():
    assert not _requires_archive_scoped_stewardship("What does stewardship mean?")
