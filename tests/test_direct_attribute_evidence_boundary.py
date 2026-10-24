"""Regression tests for direct-attribute source evidence."""
from guide_direct_attribute_evidence import (
    direct_attribute_phrase,
    direct_attribute_supported,
    should_fail_closed,
    archive_limitation_response,
    select_authoritative_doorway,
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
        "text": "At sea level, the boiling point of water changes with atmospheric pressure.",
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


def test_direct_attribute_question_rejects_unverified_preselected_primary():
    preselected = {"title": "Frequency Water", "url": "https://geralddaquila.com/frequency-water/"}
    calls = []

    def selector(query, context):
        calls.append((query, context))
        return None

    selected = select_authoritative_doorway(
        "What is the boiling point of water at sea level?",
        preselected,
        selector,
        {"documents": []},
        resource_query="What is the boiling point of water at sea level?",
    )
    assert selected is None
    assert len(calls) == 1


def test_relevant_direct_attribute_source_can_be_selected():
    preselected = {"title": "Frequency Water", "url": "https://geralddaquila.com/frequency-water/"}
    relevant = {"title": "Water properties", "url": "https://geralddaquila.com/water-properties/"}
    selected = select_authoritative_doorway(
        "What is the boiling point of water at sea level?",
        preselected,
        lambda query, context: relevant,
        {},
        normalize=lambda item: item,
    )
    assert selected == relevant


def test_ordinary_question_preserves_preselected_primary():
    preselected = {"title": "Community care", "url": "https://geralddaquila.com/community-care/"}
    calls = []
    selected = select_authoritative_doorway(
        "How can a community care for its members?",
        preselected,
        lambda query, context: calls.append(query) or None,
        {},
    )
    assert selected is preselected
    assert calls == []



def test_direct_attribute_requires_explicit_question_condition():
    from guide_direct_attribute_evidence import direct_attribute_supported

    question = "What is the boiling point of water at sea level?"
    generic = {"title": "Water properties", "text": "The boiling point of water changes with atmospheric pressure."}
    specific = {"title": "Water properties", "text": "At sea level, the boiling point of water is described here."}
    assert not direct_attribute_supported(question, generic)
    assert direct_attribute_supported(question, specific)


def test_single_word_attribute_is_still_checked():
    from guide_direct_attribute_evidence import direct_attribute_phrase, direct_attribute_supported

    question = "What is the color of the flag?"
    assert direct_attribute_phrase(question) == "color"
    assert not direct_attribute_supported(question, {"title": "Flag", "text": "The flag is displayed outside."})
    assert direct_attribute_supported(question, {"title": "Flag", "text": "The color of the flag is blue."})
