import archive_glossary_authority as glossary


def test_extracts_exact_law_of_one_entry_and_category():
    markup = """
    <h3><strong>Law of One</strong></h3>
    <h2>Principle / Ethical Orientation</h2>
    <p>A unifying principle expressing interconnectedness.</p>
    <p>Unity is relational coherence, not sameness.</p>
    <h3>Lemuria</h3>
    <p>A separate entry.</p>
    """
    entry = glossary.extract_glossary_entry(markup, "Law of One")
    assert entry is not None
    assert entry["term"] == "Law of One"
    assert entry["category"] == "Principle / Ethical Orientation"
    assert entry["paragraphs"] == [
        "A unifying principle expressing interconnectedness.",
        "Unity is relational coherence, not sameness.",
    ]


def test_does_not_fuzzy_match_a_different_term():
    markup = "<h3>Law of One</h3><p>Canonical entry.</p>"
    assert glossary.extract_glossary_entry(markup, "One Law") is None


def test_composes_three_purposeful_paragraphs_without_generic_operational_injection():
    entry = {
        "term": "Law of One",
        "category": "Principle / Ethical Orientation",
        "paragraphs": [
            "A unifying principle expressing interconnectedness.",
            "Unity is relational coherence, not sameness.",
        ],
    }
    answer = glossary.compose_glossary_recovery(entry)
    paragraphs = answer.split("\n\n")
    assert len(paragraphs) == 3
    assert "knowledge, responsibilities, or ways of working" not in answer
    assert "not a universal dictionary definition" in paragraphs[-1]
    assert "not sameness" in paragraphs[1]
