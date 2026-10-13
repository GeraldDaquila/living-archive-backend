import main


def test_relational_return_requires_topic_fit():
    query = "My partner is quiet and I feel rejection; silence is not proof of intention."
    relevant = {"title": "Silence and Rejection After Conflict", "text": "In relationships, silence can trigger rejection; distinguish observation from assumption."}
    unrelated = {"title": "Everyone Against Everyone", "text": "A broad essay about group conflict and social disagreement."}
    assert main._relational_return_direct_topic_fit(query, relevant)
    assert not main._relational_return_direct_topic_fit(query, unrelated)


def test_empty_query_cannot_gift_resource():
    doc = {"title": "General Relationship Guidance", "text": "A broad overview of relationships."}
    assert not main._relational_return_direct_topic_fit("", doc)


def test_real_nonrelational_topic_still_matches():
    query = "How can I plan a community meeting?"
    doc = {"title": "Meeting Facilitation", "text": "A practical guide to planning and facilitating a community meeting."}
    assert main._relational_return_direct_topic_fit(query, doc)


def test_broad_family_doorway_rejects_scattered_topic_mentions():
    query = "My partner is quiet and I feel rejection; silence is not proof of intention."
    broad = {
        "title": "Sovereignty in the Smallest Temple: The Couple & The Family",
        "text": (
            "Family life changes over time. Silence is one way people communicate. "
            "Rejection can shape how someone feels. Intention is not always visible."
        ),
    }
    # The old whole-document token count accepted this despite no single passage
    # connecting the visitor's specific relational terrain.
    assert not main._relational_return_direct_topic_fit(query, broad)


def test_direct_sentence_evidence_can_match_without_title_keyword():
    query = "My partner is quiet and I feel rejection; silence is not proof of intention."
    relevant = {
        "title": "A Family Conversation",
        "text": (
            "When a partner grows quiet after conflict, silence can feel like rejection, "
            "but it does not establish intention."
        ),
    }
    assert main._relational_return_direct_topic_fit(query, relevant)



def test_rejected_broad_vector_candidate_retries_bounded_conflict_search(monkeypatch):
    original = (
        "I keep trying to explain why the same argument hurts me, but we end up "
        "arguing about whether I should still feel hurt."
    )
    direct_topic = original + " The discussion shifts to how those words were said."
    repair_resource = {
        "title": "Repair Before Withdrawal",
        "text": (
            "When a conflict returns, repair can restore conversation after hurt. "
            "Relationships need listening and acknowledgement."
        ),
        "url": "https://geralddaquila.com/2026/02/04/repair-before-withdrawal/",
    }
    calls = []

    def recover(question, direct_query, profile):
        calls.append((question, direct_query))
        return repair_resource, [repair_resource]

    monkeypatch.setattr(main, "_relational_return_search_recovery", recover)
    profile = main._base._inquiry_profile(direct_topic)
    profile["action"] = "recommendation"
    profile["recommendation"] = 0.95
    profile["primary"] = "relational"
    profile["relational"] = True

    primary, outward = main._relational_return_retry_after_broad_candidate(
        None, [], original, direct_topic, profile
    )

    assert len(calls) == 1
    assert primary == repair_resource
    assert outward == [repair_resource]


def test_conflict_retry_rejects_a_broad_search_result(monkeypatch):
    original = (
        "I keep trying to explain why the same argument hurts me, but we end up "
        "arguing about whether I should still feel hurt."
    )
    broad_resource = {
        "title": "What If Everyone Is Certain Except Me?",
        "text": "A broad reflection about certainty and interpretation.",
        "url": "https://geralddaquila.com/what-if-everyone-is-certain-except-me/",
    }
    monkeypatch.setattr(
        main,
        "_relational_return_search_recovery",
        lambda question, direct_query, profile: (broad_resource, [broad_resource]),
    )
    primary, outward = main._relational_return_retry_after_broad_candidate(
        None, [], original, original, {}
    )
    assert primary is None
    assert outward == []
