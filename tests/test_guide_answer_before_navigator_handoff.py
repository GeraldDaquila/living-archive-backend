"""Regression tests: substantive topic intent must precede generic Navigator handoff."""
import main


NEWCOMER_WITH_SUBJECT = (
    "I'm new to the Living Archive. I care about healthier communities, "
    "but I don't know its vocabulary or where to begin."
)


def test_newcomer_query_with_clear_subject_is_not_orientation_only():
    assert main._is_navigator_orientation_request(NEWCOMER_WITH_SUBJECT)
    assert main._has_substantive_topic_intent(NEWCOMER_WITH_SUBJECT)


def test_topic_question_is_answer_first_even_when_archive_orientation_is_present():
    queries = (
        "I'm new to the Living Archive and want to understand healthier communities.",
        "I am new here. I want to know about trust and healthy communities.",
        "I'm new to this site. How do I recognize a healthy community?",
        "I care about healthier communities, but don't know where to begin.",
    )
    for query in queries:
        assert main._has_substantive_topic_intent(query)


def test_pure_orientation_requests_still_route_to_navigator():
    queries = (
        "I'm new to the Living Archive. Where should I begin?",
        "I'm new here and don't know how to navigate this site.",
        "Where is a good place to start exploring the Living Archive?",
    )
    for query in queries:
        assert main._is_navigator_orientation_request(query)
        assert not main._has_substantive_topic_intent(query)


def test_topic_bearing_query_does_not_erase_optional_orientation_need():
    # This invariant documents the intended split: keep the topic answer in
    # The Guide; orientation can still be offered as a deepening option later.
    assert main._has_substantive_topic_intent(NEWCOMER_WITH_SUBJECT)
