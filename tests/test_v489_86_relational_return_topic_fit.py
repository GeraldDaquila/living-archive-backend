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


def test_recurring_argument_search_recovery_uses_bounded_query_variants(monkeypatch):
    original = (
        "I keep trying to explain why the same argument hurts me, but we end up "
        "arguing about whether I should still feel hurt."
    )
    direct_topic = (
        original
        + " The focus shifts from what was said to defending tone, and the hurt "
        "is no longer discussed."
    )
    repair_resource = {
        "title": "Repair Before Withdrawal",
        "text": (
            "When a conflict returns, repair can restore conversation after hurt. "
            "Relationships need listening and acknowledgement."
        ),
        "url": "https://geralddaquila.com/2026/02/04/repair-before-withdrawal/",
    }
    queries = []

    def candidates(query, *, limit=3):
        queries.append(query)
        return [repair_resource] if query == "conflict repair" else []

    monkeypatch.setattr(main, "_wordpress_search_canonical_candidates", candidates)
    profile = main._base._inquiry_profile(direct_topic)
    profile["action"] = "recommendation"
    profile["recommendation"] = 0.95
    profile["primary"] = "relational"
    profile["relational"] = True

    primary, outward = main._relational_return_search_recovery(
        original, direct_topic, profile
    )

    assert queries == ["relationship repair", "conflict repair", "argument hurt"]
    assert primary is not None
    assert primary["title"] == "Repair Before Withdrawal"
    assert any(doc["url"] == repair_resource["url"] for doc in outward)



def test_recurring_argument_recovery_applies_specific_topic_gates_before_generic_outward_filter(monkeypatch):
    original = (
        "I keep trying to explain why the same argument hurts me, but we end up "
        "arguing about whether I should still feel hurt."
    )
    direct_topic = original + " The focus shifts from what was said to defending tone."
    repair_resource = {
        "title": "Repair Before Withdrawal",
        "text": (
            "When a conflict returns, repair can restore conversation after hurt. "
            "Relationships need listening and acknowledgement."
        ),
        "url": "https://geralddaquila.com/2026/02/04/repair-before-withdrawal/",
    }
    monkeypatch.setattr(
        main, "_wordpress_search_canonical_candidates",
        lambda query, *, limit=3: [repair_resource] if query == "conflict repair" else [],
    )
    # The ordinary outward sanitizer may reject the resource because its generic
    # profile is not the authority for this terminal HRN-return contract.
    monkeypatch.setattr(main, "_sanitize_outward_context", lambda query, docs, profile: [])
    profile = main._base._inquiry_profile(direct_topic)
    profile["action"] = "recommendation"
    profile["recommendation"] = 0.95
    profile["primary"] = "relational"
    profile["relational"] = True

    primary, outward = main._relational_return_search_recovery(original, direct_topic, profile)
    assert primary is not None
    assert primary["title"] == "Repair Before Withdrawal"
    assert outward == [repair_resource]



def test_recurring_argument_search_recovery_still_rejects_broad_decoys(monkeypatch):
    original = (
        "I keep trying to explain why the same argument hurts me, but we end up "
        "arguing about whether I should still feel hurt."
    )
    broad_resource = {
        "title": "Glyph of Resonant Governance",
        "text": "Governance supports communication and shared responsibility.",
        "url": "https://geralddaquila.com/glyph-of-resonant-governance/",
    }

    monkeypatch.setattr(
        main,
        "_wordpress_search_canonical_candidates",
        lambda query, *, limit=3: [broad_resource],
    )
    profile = main._base._inquiry_profile(original)
    profile["action"] = "recommendation"
    profile["recommendation"] = 0.95
    profile["primary"] = "relational"
    profile["relational"] = True

    primary, outward = main._relational_return_search_recovery(
        original, original, profile
    )

    assert primary is None
    assert outward == []

def test_completed_hrn_return_rejects_generic_orientation_even_with_incidental_body_overlap():
    query = (
        "The project scope changed after the agreed deadline. I feel held to the old "
        "agreement, and when I raise the changed work the conversation turns to whether "
        "I am being unreasonable. I want to see the relationship pattern more clearly."
    )
    generic_orientation = {
        "title": "🧭Orientation",
        "text": (
            "The Living Archive offers orientation to change, work, relationships, "
            "agreements, and the human experience. Start with what matters to you."
        ),
        "url": "https://geralddaquila.com/orientation/",
    }
    assert main._relational_return_is_generic_doorway(generic_orientation)
    assert not main._relational_return_direct_topic_fit(query, generic_orientation)
    assert not main._relational_return_earned_focus_fit(query, generic_orientation)


def test_completed_hrn_return_still_accepts_a_specific_resource():
    query = (
        "The project scope changed after the agreed deadline. I feel held to the old "
        "agreement, and when I raise the changed work the conversation turns to whether "
        "I am being unreasonable. I want to see the relationship pattern more clearly."
    )
    specific_resource = {
        "title": "When Agreements Change",
        "text": (
            "In relationships and collaborative work, a change to an agreement can "
            "create conflict when responsibility and expectations are no longer shared."
        ),
        "url": "https://geralddaquila.com/example/when-agreements-change/",
    }
    assert not main._relational_return_is_generic_doorway(specific_resource)


def test_workplace_scope_change_return_accepts_specific_conflict_asset():
    query = (
        "I keep returning to the agreed deadline because the project scope changed afterward. "
        "My colleague says I am making too much of it. I want to understand what is happening between us."
    )
    conflict_trust_arc = {
        "title": "ARC I: The real problem isn't conflict. It's the conversations your system is not designed to hold.",
        "text": (
            "Most teams do not fail because of disagreement. They fail because disagreement is avoided "
            "until it becomes unmanageable. This is a structural problem in how teams hold difficult conversations."
        ),
        "url": "https://geralddaquila.com/conflict-trust-arc/",
    }
    assert main._relational_return_workplace_change_focus(query)
    assert main._relational_return_workplace_change_fit(query, conflict_trust_arc)
    assert main._relational_return_direct_topic_fit(query, conflict_trust_arc)
    assert main._relational_return_earned_focus_fit(query, conflict_trust_arc)


def test_workplace_scope_change_search_recovery_uses_bounded_queries(monkeypatch):
    original = (
        "I keep returning to the agreed deadline because the project scope changed afterward. "
        "My colleague says I am making too much of it. I want to understand what is happening between us."
    )
    conflict_trust_arc = {
        "title": "ARC I: The real problem isn't conflict. It's the conversations your system is not designed to hold.",
        "text": (
            "Most teams do not fail because of disagreement. They fail because disagreement is avoided "
            "until it becomes unmanageable. This is a structural problem in how teams hold difficult conversations."
        ),
        "url": "https://geralddaquila.com/conflict-trust-arc/",
    }
    queries = []

    def candidates(query, *, limit=3):
        queries.append(query)
        return [conflict_trust_arc] if query == "workplace conflict" else []

    monkeypatch.setattr(main, "_wordpress_search_canonical_candidates", candidates)
    profile = main._base._inquiry_profile(original)
    profile["action"] = "recommendation"
    profile["recommendation"] = 0.95
    profile["primary"] = "relational"
    profile["relational"] = True

    primary, outward = main._relational_return_search_recovery(original, original, profile)

    assert queries == ["workplace conflict", "project scope agreement", "conflict moment"]
    assert primary is not None
    assert primary["title"] == conflict_trust_arc["title"]
    assert outward == [conflict_trust_arc]

