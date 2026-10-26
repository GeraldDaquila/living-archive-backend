"""Regression tests for the system-wide answer-then-doorway contract."""

from general_guide_gold_standards import resolve_exact_gold_standard
from main import _enforce_registered_gold_standard_doorway


def test_blank_gold_standard_doorway_does_not_disable_default_relevant_doorway():
    standard = resolve_exact_gold_standard(
        "What is the role of operational discipline in humane leadership?"
    )
    assert standard is not None
    assert standard["doorway_title"] == ""
    assert standard["forbids_doorway"] is False

    candidate = {
        "title": "Foundational Stewardship Cases",
        "url": "https://geralddaquila.com/level-1-case-catalog/",
    }
    assert _enforce_registered_gold_standard_doorway(candidate, standard) == candidate


def test_explicit_no_handoff_gold_standard_still_suppresses_doorway():
    standard = resolve_exact_gold_standard(
        "Explain stewardship, but do not send me to another page."
    )
    assert standard is not None
    assert standard["forbids_doorway"] is True

    candidate = {
        "title": "Foundational Stewardship Cases",
        "url": "https://geralddaquila.com/level-1-case-catalog/",
    }
    assert _enforce_registered_gold_standard_doorway(candidate, standard) is None
