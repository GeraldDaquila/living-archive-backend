import pytest

from general_guide_composition import (
    _has_intergenerational_stewardship_explanation,
    _intergenerational_stewardship_recovery,
    _parse_factory,
    _requires_intergenerational_stewardship,
    enforce_response_contracts,
)


QUESTION = "How does stewardship relate to intergenerational responsibility?"

SCREENSHOT_REGRESSION = (
    "One useful place to begin is with how our view of the world shapes the way we live. "
    "Discover how stewardship becomes the faithful practice of participating within constitutional order "
    "through responsibility, cultivation, reciprocity, and enduring care. Rather than understanding "
    "stewardship primarily as management or caretaking, this constitutional understanding emphasizes "
    "participation within an enduring order that continually invites responsibility, reciprocity, and "
    "long-term care. Institutional stewardship therefore measures success not only through performance, "
    "efficiency, or growth, but through the enduring quality of the relationships, capabilities, legitimacy, "
    "and responsibility that institutions leave behind."
)

SCREENSHOT_GARDEN_FALLBACK = (
    "Trust helps people in a community rely on one another. It gives people confidence that others will do their part and act with care. "
    "Stewardship is the shared responsibility to care for what people depend on.\n\n"
    "Think of a shared garden. Trust means people can count on one another to show up and do their part. "
    "Stewardship is tending the garden so it remains healthy for everyone. Trust makes cooperation possible; stewardship helps that cooperation endure."
)



def test_recognizes_intergenerational_stewardship_without_overcapturing():
    assert _requires_intergenerational_stewardship(QUESTION)
    assert _requires_intergenerational_stewardship(
        "Why does stewardship matter for future generations?"
    )
    assert not _requires_intergenerational_stewardship("What is stewardship?")
    assert not _requires_intergenerational_stewardship(
        "How does trust relate to accountability?"
    )


def test_single_paragraph_screenshot_regression_is_recovered_structurally():
    recovered = enforce_response_contracts(QUESTION, SCREENSHOT_REGRESSION)
    assert recovered != SCREENSHOT_REGRESSION
    assert _has_intergenerational_stewardship_explanation(recovered)
    assert len(recovered.split("\n\n")) == 3


def test_recovery_explains_relationship_example_and_bounded_responsibility():
    answer = _intergenerational_stewardship_recovery()
    assert _has_intergenerational_stewardship_explanation(answer)
    assert len(answer.split("\n\n")) == 3
    for concept in (
        "what remains possible", "future generations", "for example",
        "conditions others will inherit", "does not mean", "within our influence",
    ):
        assert concept in answer.casefold()


def test_complete_three_paragraph_answer_is_preserved():
    answer = _intergenerational_stewardship_recovery()
    assert enforce_response_contracts(QUESTION, answer) == answer


def test_live_screenshot_garden_fallback_is_replaced_by_gold_standard():
    recovered = enforce_response_contracts(QUESTION, SCREENSHOT_GARDEN_FALLBACK)
    assert recovered != SCREENSHOT_GARDEN_FALLBACK
    assert _has_intergenerational_stewardship_explanation(recovered)
    paragraphs = [p.strip() for p in recovered.split("\n\n") if p.strip()]
    assert len(paragraphs) == 3
    assert "future generations" in recovered.casefold()
    assert "does not mean" in recovered.casefold()

def test_incomplete_single_paragraph_is_not_accepted():
    assert not _has_intergenerational_stewardship_explanation(
        "Stewardship means caring responsibly for what we have today and later."
    )
