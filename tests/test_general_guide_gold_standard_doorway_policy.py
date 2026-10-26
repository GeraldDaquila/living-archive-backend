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



def test_gold_standard_title_without_url_never_becomes_null_url_doorway():
    standard = {
        "doorway_title": "Leadership Beyond Control: The Rise of Coherence-Based Governance",
        "doorway_url": "",
        "forbids_doorway": False,
    }
    independently_verified = {
        "title": "A Canonical Systems Resource",
        "url": "https://geralddaquila.com/a-canonical-systems-resource/",
    }

    assert main._apply_registered_gold_standard_doorway(
        independently_verified, standard
    ) == independently_verified
    assert main._apply_registered_gold_standard_doorway(None, standard) is None


def test_complete_gold_standard_doorway_pair_can_override_verified_selection():
    standard = {
        "doorway_title": "Approved Canonical Resource",
        "doorway_url": "https://geralddaquila.com/approved-canonical-resource/",
        "forbids_doorway": False,
    }
    independently_verified = {
        "title": "Other Canonical Resource",
        "url": "https://geralddaquila.com/other-canonical-resource/",
    }

    assert main._apply_registered_gold_standard_doorway(
        independently_verified, standard
    ) == {
        "title": "Approved Canonical Resource",
        "url": "https://geralddaquila.com/approved-canonical-resource/",
    }


def test_gold_standard_invalid_url_cannot_override_verified_selection():
    standard = {
        "doorway_title": "Unverified Resource",
        "doorway_url": "https://example.org/unverified-resource/",
        "forbids_doorway": False,
    }
    independently_verified = {
        "title": "Relevant Archive Resource",
        "url": "https://geralddaquila.com/relevant-archive-resource/",
    }

    assert main._apply_registered_gold_standard_doorway(
        independently_verified, standard
    ) == independently_verified


def test_gold_standard_explicit_no_handoff_suppresses_every_doorway():
    standard = {
        "doorway_title": "",
        "doorway_url": "",
        "forbids_doorway": True,
    }
    independently_verified = {
        "title": "Relevant Archive Resource",
        "url": "https://geralddaquila.com/relevant-archive-resource/",
    }

    assert main._apply_registered_gold_standard_doorway(
        independently_verified, standard
    ) is None
