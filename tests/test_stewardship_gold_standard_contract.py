from general_guide_composition import enforce_response_contracts, _archive_scoped_stewardship_recovery, _requires_archive_scoped_stewardship


QUESTION = "What does stewardship mean in the Living Archive?"


def test_archive_stewardship_recovery_expresses_stewardship_follows_understanding():
    answer = _archive_scoped_stewardship_recovery()
    paragraphs = [p.strip() for p in answer.split("\n\n") if p.strip()]
    assert len(paragraphs) == 3
    assert "stewardship follows understanding" in paragraphs[0].lower()
    assert "what has been entrusted to us" in paragraphs[0].lower()
    assert "keeping a promise" in paragraphs[1].lower()
    assert "no worse and ideally better" in paragraphs[2].lower()
    assert "For example" in paragraphs[1]
    assert "controlling everything or sacrificing yourself" in paragraphs[2]
    assert "general explanation rather than" not in answer


def test_observed_bad_answer_is_replaced_with_canonical_recovery():
    old = (
        "Stewardship mean in the Living Archive is best understood by what it means "
        "and how it operates in practice. A useful definition distinguishes the idea "
        "from nearby concepts and makes its implications clear. The precise meaning "
        "can vary by field or institution, so this is a general explanation rather "
        "than a claim that the Living Archive uses a particular formal definition."
    )
    assert enforce_response_contracts(QUESTION, old) == _archive_scoped_stewardship_recovery()


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
