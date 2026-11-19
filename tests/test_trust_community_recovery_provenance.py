"""Regression coverage for truthful provenance on the trust/community recovery route."""

def test_trust_community_recovery_is_conceptual_not_archive_supported():
    import main
    from gold_star_evidence_validation import build_evidence_assessment

    query = "What is the role of trust in community stewardship?"
    contract = main._trust_community_stewardship_final_contract(query)

    assert contract is not None
    assert contract["answer_basis"]["kind"] == "general_knowledge"
    assert "not represented as the source" in contract["answer_basis"]["explanation"]
    assert contract["recommendation"]["title"] == (
        "Trust Architecture: The Missing Infrastructure Behind Functional Societies"
    )
    assert contract["recommendation"]["url"].startswith("https://geralddaquila.com/")

    refs, assessment = build_evidence_assessment(
        query, contract["response"], contract["answer_basis"], []
    )
    assert refs == []
    assert assessment["status"] == "not_applicable"


def test_trust_community_recovery_keeps_archive_doorway_separate_from_answer_provenance():
    import main

    query = "What is the role of trust in community stewardship?"
    contract = main._trust_community_stewardship_final_contract(query)

    assert contract["answer_basis"]["kind"] != "archive_supported"
    assert "source_url" not in contract["answer_basis"]
    assert contract["recommendation"]["kind"] == "archive_resource"
