"""Regression tests for Guide discovery phrasing and source quotation cleanup."""
import main


def test_study_itself_phrase_extracts_subject():
    assert main._guide_subject_discovery_query(
        "I want the study itself on Political Dynasties in the Philippines."
    ) == "Political Dynasties in the Philippines"


def test_recommend_named_article_extracts_subject():
    assert main._guide_subject_discovery_query(
        "Please recommend the article titled Political Dynasties in the Philippines."
    ) == "Political Dynasties in the Philippines"


def test_existing_broad_reading_query_remains_discovery():
    assert main._guide_subject_discovery_query(
        "I want to understand how political dynasties affect public accountability "
        "in the Philippines. What should I read?"
    ) == "how political dynasties affect public accountability in the Philippines"


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
    ) == "Political Dynasties in the Philippines"


def test_title_only_query_is_resource_discovery():
    assert main._guide_subject_discovery_query(
        "Political Dynasties in the Philippines"
    ) == "Political Dynasties in the Philippines"
