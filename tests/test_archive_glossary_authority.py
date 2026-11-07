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


def test_definition_recovery_prefers_live_glossary_over_competing_local_definition(monkeypatch):
    import deterministic_answer_recovery as recovery

    entry = {
        "term": "Law of One",
        "category": "Principle / Ethical Orientation",
        "paragraphs": [
            "A unifying principle expressing the inherent interconnectedness of all existence. "
            "It is an ethical and perceptual orientation, not a doctrine or external authority.",
            "Unity is understood as relational coherence, not sameness, fusion, or loss of agency.",
        ],
    }
    monkeypatch.setattr(glossary, "get_glossary_entry", lambda subject: entry)
    answer = recovery.compose_definition_significance("Law of One")
    assert len(answer.split("\n\n")) == 3
    assert "inherent interconnectedness" in answer
    assert "not sameness" in answer
    assert "Ra Material" not in answer
    assert "knowledge, responsibilities, or ways of working" not in answer


def test_extracts_direct_permalink_anchor_for_exact_glossary_heading():
    markup = """
    <h3 id="law-of-one"><strong>Law of One</strong></h3>
    <h2>Principle / Ethical Orientation</h2>
    <p>A unifying principle.</p>
    """
    entry = glossary.extract_glossary_entry(markup, "Law of One")
    assert entry["source_url"] == "https://geralddaquila.com/glossary/#law-of-one"
    assert entry["source_anchor"] == "law-of-one"


def test_glossary_entry_without_anchor_uses_valid_glossary_page_url():
    entry = glossary.extract_glossary_entry(
        "<h3><strong>Stewardship</strong></h3><p>Care with responsibility.</p>",
        "Stewardship",
    )
    assert entry["source_url"] == "https://geralddaquila.com/glossary/"
    assert entry["source_anchor"] == ""
