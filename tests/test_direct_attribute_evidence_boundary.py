"""Regression tests for direct-attribute source evidence."""
from guide_direct_attribute_evidence import (
    direct_attribute_phrase,
    direct_attribute_supported,
    should_fail_closed,
    archive_limitation_response,
)


def test_direct_attribute_question_extracts_requested_property():
    assert direct_attribute_phrase("What is the boiling point of water at sea level?") == "boiling point"


def test_entity_overlap_does_not_substitute_for_requested_attribute():
    decoy = {
        "title": "Frequency Water",
        "url": "https://geralddaquila.com/frequency-water/",
        "text": "Water is explored as liquid memory, healing, frequency, and mission.",
    }
    assert not direct_attribute_supported(
        "What is the boiling point of water at sea level?", decoy
    )


def test_source_that_discusses_requested_attribute_can_qualify():
    source = {
        "title": "Water properties",
        "url": "https://geralddaquila.com/water-properties/",
        "text": "The boiling point of water changes with atmospheric pressure.",
    }
    assert direct_attribute_supported(
        "What is the boiling point of water at sea level?", source
    )


def test_non_attribute_question_is_not_restricted_by_this_contract():
    assert direct_attribute_supported(
        "How can a community care for its members?",
        {"title": "Community care", "text": "A community can care through trust and reciprocity."},
    )


def test_ordinary_inquiry_fails_closed_when_archive_evidence_is_unavailable():
    assert should_fail_closed(True, discovery_subject=False)
    response = archive_limitation_response()
    assert "Living Archive" in response
    assert "outside knowledge" in response


def test_successfully_grounded_ordinary_inquiry_does_not_use_no_evidence_fallback():
    assert not should_fail_closed(False, discovery_subject=False)


def test_subject_discovery_uses_its_separate_canonical_page_evidence_gate():
    assert not should_fail_closed(True, discovery_subject=True)
