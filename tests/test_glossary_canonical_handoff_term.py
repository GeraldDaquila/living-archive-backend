"""Regression coverage for canonical Glossary handoff term extraction."""
import main


def test_canonical_glossary_definition_extracts_only_the_canonical_term():
    queries = (
        "What is the canonical Glossary definition of stewardship?",
        "What is the Glossary definition of stewardship?",
        "Show me the canonical Glossary definition for stewardship.",
        "What is the canonical Living Archive Glossary entry on stewardship?",
    )
    for query in queries:
        assert main._normalize_glossary_term(query) == "stewardship"


def test_glossary_definition_term_extraction_preserves_multiword_terms():
    assert (
        main._normalize_glossary_term(
            "What is the canonical Glossary definition of knowledge stewardship?"
        )
        == "knowledge stewardship"
    )


def test_existing_simple_definition_extraction_remains_unchanged():
    assert main._normalize_glossary_term("What does stewardship mean?") == "stewardship"
