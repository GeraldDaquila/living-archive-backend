"""Regression tests for Guide discovery voice and concrete concept explanations."""

import main


def test_direct_discovery_uses_natural_grounded_language_and_exact_quote():
    title = "Political Dynasties in the Philippines"
    quote = (
        "Why do political dynasties remain deeply embedded in Philippine "
        "governance despite ongoing calls for reform?"
    )
    answer = main._guide_deterministic_discovery_response(
        "political dynasties affect public accountability in the Philippines",
        {"title": title, "url": "https://geralddaquila.com/political-dynasties/"},
        [{
            "title": title,
            "text": quote,
            "_discovery_relevance": "direct",
        }],
    )

    assert answer.startswith(f"{title} is a useful place to begin.")
    assert f"“{quote}”" in answer
    assert "strongest direct match I found" not in answer
    assert "subject-fit check" not in answer
    assert "That gives you a focused entry point" in answer


def test_direct_discovery_does_not_invent_quote_when_no_complete_sentence_exists():
    title = "Political Dynasties in the Philippines"
    answer = main._guide_deterministic_discovery_response(
        "political dynasties in the Philippines",
        {"title": title, "url": "https://geralddaquila.com/political-dynasties/"},
        [{
            "title": title,
            "text": "Political dynasties remain deeply embedded in governance",
            "_discovery_relevance": "direct",
        }],
    )

    assert title in answer
    assert "won’t manufacture one" in answer
    assert "“" not in answer


def test_related_discovery_does_not_overstate_relevance():
    answer = main._guide_deterministic_discovery_response(
        "political dynasties and accountability",
        {"title": "Governance in the Philippines"},
        [{
            "text": "The essay discusses governance and accountability.",
            "_discovery_relevance": "related",
            "_discovery_support_terms": ["governance", "accountability"],
        }],
    )

    assert "couldn’t verify a page that directly covers" in answer
    assert "A related place to explore is Governance in the Philippines." in answer
    assert "does not establish that it directly addresses your question" in answer


def test_abstract_archive_definition_requires_everyday_example_and_paragraph_breaks():
    from general_guide_composition import _has_everyday_example, _requires_concrete_concept_explanation

    query = "What does reciprocity mean in the Living Archive?"
    assert _requires_concrete_concept_explanation(query)
    assert _has_everyday_example(
        "Reciprocity is mutual support, not a tally of favors.\\n\\n"
        "Imagine neighbors taking turns checking on an older resident.\\n\\n"
        "Contributions need not be equal every time."
    )


def test_simple_factual_question_is_not_forced_into_concept_template():
    from general_guide_composition import _requires_concrete_concept_explanation

    assert not _requires_concrete_concept_explanation("What is the capital of the Philippines?")
    assert not _requires_concrete_concept_explanation("List the forms of reciprocity.")
