"""Regression tests for relevance-safe HRN return gifts."""

import main


def test_projection_return_requires_direct_projection_or_observation_inference_evidence():
    query = "I can't tell whether what I'm sensing in a relationship is real or something I'm projecting."
    projection_article = {
        "title": "Projection: The Mirror of Our Inner Shadows",
        "text": "Projection in relationships can blur what is observed and what is inferred about the other person.",
        "url": "https://geralddaquila.com/2025/06/04/projection-the-mirror-of-our-inner-shadows/",
    }
    agency_article = {
        "title": "Being in the Driver's Seat (Without Pretending You Control the Road)",
        "text": "Agency is the difference between what a person can influence and what remains outside their control.",
        "url": "https://geralddaquila.com/2026/01/20/being-in-the-drivers-seat-without-pretending-you-control-the-road/",
    }
    assert main._relational_return_direct_topic_fit(query, projection_article) is True
    assert main._relational_return_direct_topic_fit(query, agency_article) is False


def test_projection_return_accepts_observation_inference_evidence_without_projection_word():
    query = "I can't tell whether what I'm sensing in a relationship is real or something I'm projecting."
    doc = {
        "title": "What You Notice and What You Infer",
        "text": "In a relationship, observation is not the same as inference or assumption about the other person.",
        "url": "https://geralddaquila.com/example/observation-inference/",
    }
    assert main._relational_return_direct_topic_fit(query, doc) is True


def test_unrelated_query_does_not_receive_projection_specific_filter():
    query = "How can I plan a community meeting?"
    doc = {
        "title": "Meeting Facilitation",
        "text": "A practical guide to planning and facilitating a community meeting.",
        "url": "https://geralddaquila.com/example/meeting-facilitation/",
    }
    assert main._relational_return_direct_topic_fit(query, doc) is True
