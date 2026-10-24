"""Regression coverage for bounded sovereignty answers during provider exhaustion."""

import main
from guide_direct_attribute_evidence import (
    direct_attribute_phrase,
    direct_attribute_supported,
    select_authoritative_doorway,
)


def test_sovereignty_definition_remains_useful_without_archive_context():
    result = main._basic_inquiry_round1_deterministic_response(
        "What does sovereignty mean in the Living Archive's approach to human relationships?",
        {},
        {"context_blocks": ""},
        recommendation_available=False,
    )

    response = result["response"].casefold()
    assert "sovereignty" in response
    assert "decisions that affect them" in response
    assert "general conceptual explanation" in response
    assert "not a verified quotation" in response
    assert result["provider"] == "bounded_general_knowledge_recovery"
    assert result["doorway_title"] == ""


def test_sovereignty_recovery_fails_closed_when_context_is_not_parseable():
    result = main._basic_inquiry_round1_deterministic_response(
        "What does sovereignty mean in the Living Archive's approach to human relationships?",
        {},
        {
            # The protected core parser expects its own context-block format;
            # arbitrary JSON is deliberately not treated as canonical evidence.
            "context_blocks": (
                '[{"title":"The Living Archive Navigator: Volume II - Governance & Sovereignty",'
                '"content":"Governance and sovereignty."}]'
            )
        },
        recommendation_available=True,
    )

    assert "general conceptual explanation" in result["response"]
    assert result["doorway_title"] == ""



def test_direct_attribute_rejects_entity_only_archive_evidence():
    question = "What is the boiling point of water at sea level?"
    assert direct_attribute_phrase(question) == "boiling point"
    decoy = {
        "title": "Frequency Water",
        "url": "https://geralddaquila.com/frequency-water/",
        "text": "Water is explored as liquid memory, healing, frequency, and mission.",
    }
    assert not direct_attribute_supported(question, decoy)


def test_direct_attribute_requires_the_explicit_condition():
    question = "What is the boiling point of water at sea level?"
    generic = {"text": "The boiling point of water changes with atmospheric pressure."}
    specific = {"text": "At sea level, the boiling point of water changes with atmospheric pressure."}
    assert not direct_attribute_supported(question, generic)
    assert direct_attribute_supported(question, specific)


def test_direct_attribute_reselects_instead_of_trusting_preselected_doorway():
    preselected = {"title": "Frequency Water", "url": "https://geralddaquila.com/frequency-water/"}
    calls = []

    def source_selector(query, context):
        calls.append(query)
        return None

    selected = select_authoritative_doorway(
        "What is the boiling point of water at sea level?",
        preselected,
        source_selector,
        {},
    )
    assert selected is None
    assert calls == ["What is the boiling point of water at sea level?"]


def test_non_attribute_question_keeps_preselected_doorway():
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
