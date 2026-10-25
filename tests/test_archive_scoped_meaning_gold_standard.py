import pytest

from general_guide_composition import (
    _requires_archive_scoped_meaning,
    enforce_response_contracts,
)


QUESTION = "What does stewardship mean in the Living Archive?"


def test_archive_scoped_meaning_is_recognized_as_its_own_quality_class():
    assert _requires_archive_scoped_meaning(QUESTION)
    assert not _requires_archive_scoped_meaning("What does stewardship mean?")
    assert not _requires_archive_scoped_meaning("Open the Glossary for stewardship")


def test_archive_scoped_meaning_rejects_one_paragraph_generic_answer():
    generic = (
        "Stewardship mean in the Living Archive is best understood by what it means "
        "and how it operates in practice. A useful definition distinguishes the idea "
        "from nearby concepts and makes its implications clear. The precise meaning "
        "can vary by field or institution, so this is a general explanation rather "
        "than a claim that the Living Archive uses a particular formal definition."
    )
    with pytest.raises(ValueError, match="three-paragraph Guide Gold Standard"):
        enforce_response_contracts(QUESTION, generic)


def test_archive_scoped_meaning_accepts_three_paragraph_answer_with_example():
    response = (
        "In the Living Archive, stewardship means taking responsibility for what has "
        "been entrusted to our care, using understanding to guide action rather than "
        "treating knowledge as an end in itself.\n\n"
        "For example, when a community shares knowledge, stewardship means preserving "
        "its context, making it useful to others, and being honest about its limits "
        "instead of extracting a claim and leaving its consequences to someone else.\n\n"
        "Stewardship is not control over everything or an obligation to carry every "
        "burden alone. It asks us to recognize what is genuinely ours to care for, "
        "act within our responsibilities, and leave what we steward more coherent "
        "and usable for those who follow."
    )
    assert enforce_response_contracts(QUESTION, response) == response
