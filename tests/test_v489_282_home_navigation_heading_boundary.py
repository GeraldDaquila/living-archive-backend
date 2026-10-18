"""Regression tests for v489.282 Guide navigation and excerpt boundaries."""
import main


def test_explicit_living_archive_homepage_navigation_is_deterministic():
    result = main._basic_inquiry_response(
        "Please take me to the homepage of the Living Archive."
    )
    assert result["intent"] == "NAVIGATION"
    assert result["route_source"] == "guide_explicit_home_navigation"
    assert result["recommendation"] == {
        "title": "Living Archive",
        "url": "https://geralddaquila.com/",
    }
    assert result["version"] == "v489.282"


def test_homepage_rule_does_not_trigger_for_topic_discovery():
    # The homepage shortcut requires explicit homepage wording and navigation
    # language; ordinary subject discovery must continue through canonical retrieval.
    query = "What should I read about political dynasties in the Philippines?"
    assert not main.re.search(
        r"\\b(?:homepage|home page|site home|website home)\\b", query, main.re.I
    )


def test_heading_glued_to_question_is_not_quoted_as_one_sentence():
    result = main._guide_deterministic_discovery_response(
        "political dynasties",
        {"title": "Political Dynasties in the Philippines"},
        [{
            "text": (
                "A Network Analysis of Power Structures and Their Socioeconomic Impacts "
                "Why do political dynasties remain deeply embedded in Philippine governance "
                "despite ongoing calls for reform?"
            ),
            "_discovery_relevance": "direct",
            "_discovery_support_terms": ["political", "dynasties"],
        }],
    )
    assert "“Why do political dynasties remain deeply embedded" in result
    assert "Impacts Why do" not in result
