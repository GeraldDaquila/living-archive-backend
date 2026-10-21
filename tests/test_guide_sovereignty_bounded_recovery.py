"""Regression coverage for bounded sovereignty answers during provider exhaustion."""

import main


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
