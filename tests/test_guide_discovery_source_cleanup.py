"""Regression tests for Guide discovery phrasing and source quotation cleanup."""
import main


def test_study_itself_phrase_extracts_subject():
    assert main._guide_subject_discovery_query(
        "I want the study itself on Political Dynasties in the Philippines."
    ) == "political dynasties in the philippines"


def test_recommend_named_article_extracts_subject():
    assert main._guide_subject_discovery_query(
        "Please recommend the article titled Political Dynasties in the Philippines."
    ) == "political dynasties in the philippines"


def test_existing_broad_reading_query_remains_discovery():
    assert main._guide_subject_discovery_query(
        "I want to understand how political dynasties affect public accountability "
        "in the Philippines. What should I read?"
    ) == "how political dynasties affect public accountability in the philippines"


def test_unrelated_question_is_not_reclassified_as_archive_discovery():
    assert main._guide_subject_discovery_query(
        "What is the capital city of Japan and what is its population?"
    ) == ""


def test_author_metadata_is_removed_before_quote_selection(monkeypatch):
    doorway = {"title": "Political Dynasties in the Philippines"}
    evidence = [{
        "_discovery_relevance": "direct",
        "text": (
            "Daquila, PhD Candidate Why do political dynasties remain deeply "
            "embedded in Philippine governance despite ongoing calls for reform? "
            "This is a complete source sentence about political dynasties and "
            "public accountability in the Philippines."
        ),
    }]
    result = main._guide_deterministic_discovery_response(
        "political dynasties in the Philippines", doorway, evidence
    )
    assert "Daquila, PhD Candidate" not in result
    assert "Its page states:" in result


def test_exact_explicit_study_request_with_title_prefix_extracts_title():
    assert main._guide_subject_discovery_query(
        "Political Dynasties in the Philippines — I want the study itself, please."
    ) == "political dynasties in the philippines"


def test_title_only_query_is_resource_discovery():
    assert main._guide_subject_discovery_query(
        "Political Dynasties in the Philippines"
    ) == "political dynasties in the philippines"


CANONICAL_POLITICAL_DYNASTIES_URL = (
    "https://geralddaquila.com/2025/05/21/"
    "political-dynasties-in-the-philippines-a-network-analysis-of-power-structures-and-their-socioeconomic-impacts/"
)


def test_registered_exact_title_beats_suffixed_duplicate(monkeypatch):
    """A title lookup must resolve the canonical study, not its decorated duplicate."""
    exact_node = {
        "node_id": "political-dynasties-philippines-study",
        "asset_type": "canonical_study",
        "title": "Political Dynasties in the Philippines",
        "canonical_url": CANONICAL_POLITICAL_DYNASTIES_URL,
        "purpose": "Study of political dynasties and Philippine governance",
        "semantic_hints": ["political dynasties", "public accountability", "Philippines"],
        "status": "active",
    }
    duplicate_node = {
        "node_id": "duplicate-display-node",
        "title": "Political Dynasties in the Philippines • Life.Understood.",
        "canonical_url": "https://geralddaquila.com/political-dynasties-overview/",
        "purpose": "Overview of political dynasties, accountability, and governance",
        "semantic_hints": ["political dynasties", "public accountability", "Philippines", "governance"],
        "status": "active",
    }
    monkeypatch.setattr(main, "_guide_registered_discovery_nodes", lambda subject, limit=3: [exact_node, duplicate_node])
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [exact_node, duplicate_node])
    documents = [
        {
            "title": exact_node["title"], "url": exact_node["canonical_url"],
            "text": ("Political dynasties shape Philippine governance and public accountability. " * 5),
            "_guide_node": exact_node,
        },
        {
            "title": duplicate_node["title"], "url": duplicate_node["canonical_url"],
            "text": ("Political dynasties shape Philippine governance, public accountability, institutions, " * 8),
            "_guide_node": duplicate_node,
        },
    ]
    doorway, evidence = main._guide_align_discovery_doorway(
        "Political Dynasties in the Philippines", documents
    )
    assert doorway == {
        "title": "Political Dynasties in the Philippines",
        "url": CANONICAL_POLITICAL_DYNASTIES_URL,
    }
    assert evidence and evidence[0]["url"] == CANONICAL_POLITICAL_DYNASTIES_URL
    assert evidence[0]["_guide_node"]["node_id"] == "political-dynasties-philippines-study"
    assert evidence[0]["_guide_node"]["asset_type"] == "canonical_study"


def test_explicit_study_request_subject_matches_canonical_permalink():
    subject = main._guide_subject_discovery_query(
        "Political Dynasties in the Philippines — I want the study itself, please."
    )
    assert subject == "political dynasties in the philippines"
    assert CANONICAL_POLITICAL_DYNASTIES_URL.endswith(
        "political-dynasties-in-the-philippines-a-network-analysis-of-power-structures-and-their-socioeconomic-impacts/"
    )



def test_html_extraction_preserves_blocks_and_removes_standalone_byline():
    source_html = """
    <article>
      <hr>
      <h2>A Network Analysis of Power Structures and Their Socioeconomic Impacts</h2>
      <p>Gerald A. Daquila, PhD Candidate</p>
      <p>Why do political dynasties remain deeply embedded in Philippine governance despite ongoing calls for reform?</p>
      <p>Political dynasties influence institutions and public accountability.</p>
    </article>
    """
    text = main._guide_html_to_source_text(source_html)
    assert "Gerald A. Daquila, PhD Candidate" not in text
    assert "A Network Analysis of Power Structures and Their Socioeconomic Impacts" in text
    assert "Why do political dynasties remain deeply embedded in Philippine governance despite ongoing calls for reform?" in text
    assert "Political dynasties influence institutions and public accountability." in text
    assert text.index("A Network Analysis") < text.index("Why do political dynasties") < text.index("Political dynasties influence")


def test_html_extraction_preserves_author_name_inside_substantive_prose():
    source_html = (
        "<p>Gerald A. Daquila, PhD Candidate</p>"
        "<p>The study was prepared by Gerald A. Daquila, PhD Candidate and discusses public accountability.</p>"
    )
    text = main._guide_html_to_source_text(source_html)
    assert text.count("Gerald A. Daquila, PhD Candidate") == 1
    assert "The study was prepared by Gerald A. Daquila, PhD Candidate and discusses public accountability." in text



def test_explicit_study_and_title_only_queries_select_exact_registered_asset(monkeypatch):
    exact_node = {
        "node_id": "political-dynasties-philippines-study",
        "asset_type": "canonical_study",
        "title": "Political Dynasties in the Philippines",
        "canonical_url": CANONICAL_POLITICAL_DYNASTIES_URL,
        "purpose": "Study of political dynasties and Philippine governance",
        "semantic_hints": ["political dynasties", "public accountability", "Philippines"],
        "status": "active",
    }
    duplicate_node = {
        "node_id": "duplicate-display-node",
        "title": "Political Dynasties in the Philippines • Life.Understood.",
        "canonical_url": "https://geralddaquila.com/political-dynasties-overview/",
        "purpose": "Overview of political dynasties, accountability, and governance",
        "semantic_hints": ["political dynasties", "public accountability", "Philippines", "governance"],
        "status": "active",
    }
    monkeypatch.setattr(main, "_guide_registered_discovery_nodes", lambda subject, limit=3: [exact_node, duplicate_node])
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [exact_node, duplicate_node])
    documents = [
        {
            "title": exact_node["title"], "url": exact_node["canonical_url"],
            "text": "Political dynasties shape Philippine governance and public accountability. " * 5,
            "_guide_node": exact_node,
        },
        {
            "title": duplicate_node["title"], "url": duplicate_node["canonical_url"],
            "text": "Political dynasties shape Philippine governance, public accountability, institutions. " * 8,
            "_guide_node": duplicate_node,
        },
    ]
    queries = (
        "Political Dynasties in the Philippines — I want the study itself, please.",
        "Political Dynasties in the Philippines",
    )
    for query in queries:
        subject = main._guide_subject_discovery_query(query)
        assert subject == "political dynasties in the philippines"
        doorway, evidence = main._guide_align_discovery_doorway(subject, documents)
        assert doorway == {
            "title": "Political Dynasties in the Philippines",
            "url": CANONICAL_POLITICAL_DYNASTIES_URL,
        }
        assert evidence and evidence[0]["url"] == CANONICAL_POLITICAL_DYNASTIES_URL
        assert evidence[0]["_guide_node"]["node_id"] == "political-dynasties-philippines-study"
        assert evidence[0]["_guide_node"]["asset_type"] == "canonical_study"



def test_discovery_doorway_requires_matching_selected_canonical_evidence():
    doorway = {
        "title": "Political Dynasties in the Philippines",
        "url": CANONICAL_POLITICAL_DYNASTIES_URL,
    }
    matching_evidence = [{
        "title": doorway["title"],
        "url": CANONICAL_POLITICAL_DYNASTIES_URL,
        "text": "Political dynasties shape Philippine governance and public accountability.",
    }]
    unrelated_evidence = [{
        "title": "Living in the Barangay",
        "url": "https://geralddaquila.com/living-in-the-barangay/",
        "text": "A different subject.",
    }]
    assert main._guide_discovery_doorway_is_evidence_backed(doorway, matching_evidence)
    assert not main._guide_discovery_doorway_is_evidence_backed(doorway, unrelated_evidence)
    assert not main._guide_discovery_doorway_is_evidence_backed(doorway, [])
    assert not main._guide_discovery_doorway_is_evidence_backed(None, matching_evidence)


def test_discovery_fallback_is_used_when_final_doorway_is_missing():
    result = main._guide_subject_discovery_answer(
        "An unrelated provider-generated answer.",
        "Political Dynasties in the Philippines",
        None,
        [],
    )
    assert "couldn’t verify a Living Archive page" in result
    assert "unrelated provider-generated answer" not in result



def test_basic_inquiry_response_suppresses_stale_discovery_recommendation(monkeypatch):
    """Exercise final response assembly when initial doorway lacks selected evidence."""
    stale_url = "https://geralddaquila.com/living-in-the-barangay/"
    stale_node = {
        "node_id": "living-in-the-barangay",
        "asset_type": "canonical_article",
        "title": "Living in the Barangay",
        "canonical_url": stale_url,
        "status": "active",
        "purpose": "A guide to barangay life",
        "semantic_hints": ["barangay", "community life"],
    }
    monkeypatch.setattr(main.general_guide_composition, "clarification_response", lambda *a, **k: None)
    monkeypatch.setattr(main.general_guide_composition, "correction_subject", lambda *a, **k: "")
    monkeypatch.setattr(main.general_guide_composition, "is_exact_source_request", lambda *a, **k: False)
    monkeypatch.setattr(
        main.use_core, "fetch_canonical_context",
        lambda query: {
            "intent": "TOPICAL_INQUIRY",
            "recommendation_canonical_primary": {
                "title": stale_node["title"], "url": stale_url
            },
            "frame_neutral_evidence_unavailable": True,
            "context_blocks": "",
        },
    )
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [stale_node])
    monkeypatch.setattr(main, "_guide_requires_canonical_subject_supplement", lambda *a, **k: True)
    monkeypatch.setattr(main, "_wordpress_search_canonical_candidates", lambda *a, **k: [])
    monkeypatch.setattr(main, "_wordpress_fetch_selected_canonical_body", lambda *a, **k: None)
    monkeypatch.setattr(main, "_guide_registered_discovery_nodes", lambda *a, **k: [])
    monkeypatch.setattr(
        main.use_core, "_frame_neutral_generation_documents",
        lambda docs, *a, **k: (docs, False),
    )
    monkeypatch.setattr(
        main.use_core, "_evidence_sufficiency_gate",
        lambda docs, *a, **k: (docs, False),
    )
    monkeypatch.setattr(
        main.use_core, "_v208_question_evidence_fit_gate",
        lambda docs, *a, **k: (docs, False),
    )
    monkeypatch.setattr(
        main.general_guide_composition, "compose",
        lambda **kwargs: {"response": "Here is a general overview of political dynasties.", "provider": "test", "model": "test"},
    )

    result = main._basic_inquiry_response(
        "Political Dynasties in the Philippines"
    )

    assert result["ok"] is True
    assert result["processing"] == "basic_inquiry"
    assert result["intent"] == "TOPICAL_INQUIRY"
    assert result["recommendation"] is None
    assert result["answer_basis"]["kind"] == "general_knowledge"
    assert "couldn’t verify a Living Archive page" in result["response"]
    assert "Living in the Barangay" not in result["response"]


def test_standalone_written_byline_is_removed_but_title_and_body_are_preserved():
    raw_html = (
        "<article>"
        "<h1>Political Dynasties in the Philippines</h1>"
        "<p>Written by Gerald A.</p>"
        "<p>A Network Analysis of Power Structures and Their Socioeconomic Impacts.</p>"
        "<p>Gerald A. Daquila argues that accountability matters in this study.</p>"
        "</article>"
    )
    cleaned = main._guide_html_to_source_text(raw_html)
    assert "Political Dynasties in the Philippines" in cleaned
    assert "A Network Analysis of Power Structures and Their Socioeconomic Impacts." in cleaned
    assert "Written by Gerald A." not in cleaned
    assert "Gerald A. Daquila argues that accountability matters in this study." in cleaned
