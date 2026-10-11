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
