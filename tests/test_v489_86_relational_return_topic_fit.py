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


def test_projection_title_is_direct_evidence_even_if_body_uses_broader_language():
    query = "I can't tell whether what I'm sensing in a relationship is real or something I'm projecting."
    doc = {
        "title": "Projection: The Mirror of Our Inner Shadows",
        "text": "A reflective essay about how people make sense of their inner experience.",
        "url": "https://geralddaquila.com/2025/06/04/projection-the-mirror-of-our-inner-shadows/",
    }
    assert main._relational_return_direct_topic_fit(query, doc) is True


def test_earlier_hurt_heard_as_blame_does_not_invent_listening_problem():
    query = (
        "Understand how raising an earlier hurt becomes a dispute about blame, "
        "without assuming either partner intends to hurt or dismiss the other. "
        "The argument changes direction when explaining an earlier hurt is heard as assigning blame."
    )
    self_sacrifice_article = {
        "title": "When Love Has Been Built on Your Self-Sacrifice",
        "text": (
            "Many relationships form around roles we step into without realizing it. "
            "You may think, 'If I stop over-giving, they will feel hurt.' "
            "You are responsible for changing with honesty and care, not with blame. "
            "There is a difference between attacking someone for the past and no longer "
            "participating in a pattern that harms you. Listen without defensiveness."
        ),
    }
    assert not main._relational_return_earned_focus_fit(query, self_sacrifice_article)
    assert not main._relational_return_direct_topic_fit(query, self_sacrifice_article)



def test_recurring_argument_return_rejects_broad_governance_glyph_decoy():
    query = (
        "I keep trying to explain why the same argument hurts me, but we end up "
        "arguing about whether I should still feel hurt. The discussion keeps "
        "moving away from what was said and toward my tone. From why do I feel "
        "this to why is my feeling being treated as a claim to be verified? "
        "Relational communication during disagreement: listening, acknowledgment, "
        "being heard, and receiving another person's point before responding."
    )
    broad_glyph = {
        "title": "Glyph of Resonant Governance",
        "text": (
            "In relationships, conflict can be held through communication. "
            "Governance invites shared responsibility and awareness."
        ),
        "url": "https://geralddaquila.com/glyph-of-resonant-governance/",
    }
    assert not main._relational_return_earned_focus_fit(query, broad_glyph)
    assert not main._relational_return_direct_topic_fit(query, broad_glyph)


def test_recurring_argument_return_keeps_direct_repair_resource():
    query = (
        "I keep trying to explain why the same argument hurts me, but we end up "
        "arguing about whether I should still feel hurt. The discussion keeps "
        "moving away from what was said and toward my tone."
    )
    repair_resource = {
        "title": "Repair Before Withdrawal",
        "text": (
            "When a conflict returns, repair can restore conversation after hurt. "
            "Relationships need listening and acknowledgement."
        ),
        "url": "https://geralddaquila.com/2026/02/04/repair-before-withdrawal/",
    }
    assert main._relational_return_direct_topic_fit(query, repair_resource)



def test_recurring_argument_final_doorway_guard_rejects_broad_title():
    query = (
        "I keep trying to explain why the same argument hurts me, but we end up "
        "arguing about whether I should still feel hurt. From why do I feel this "
        "to why is my feeling being treated as a claim to be verified? Relational "
        "communication during disagreement: listening, acknowledgment, being heard, "
        "and receiving another person's point before responding."
    )
    broad_glyph = {
        "title": "Glyph of Resonant Governance",
        "text": "In relationships, conflict can be held through communication. Governance invites shared responsibility and awareness.",
    }
    direct_repair = {
        "title": "Repair Before Withdrawal",
        "text": "When a conflict returns, repair can restore conversation after hurt. Relationships need listening and acknowledgement.",
    }
    assert not main._relational_return_direct_topic_fit(query, broad_glyph)
    assert main._relational_return_direct_topic_fit(query, direct_repair)



def test_explicit_feeling_unheard_still_qualifies_for_listening_resource():
    query = "I feel unheard when my partner goes silent after an argument. I want to know whether they are listening."
    listening_article = {
        "title": "Silence and Rejection After Conflict",
        "text": (
            "In relationships, silence after conflict can feel like rejection. "
            "Listening and acknowledgment can help people feel heard without assuming intention."
        ),
    }
    assert main._relational_return_earned_focus_fit(query, listening_article)
    assert main._relational_return_direct_topic_fit(query, listening_article)
