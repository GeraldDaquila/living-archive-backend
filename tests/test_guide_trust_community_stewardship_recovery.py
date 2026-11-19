"""Final visitor contract for the trust/community stewardship question."""

from pathlib import Path

import main


QUERY = "What is the role of trust in community stewardship?"


def test_trust_community_stewardship_contract_answers_with_humane_concrete_language():
    contract = main._trust_community_stewardship_final_contract(QUERY)
    assert contract is not None
    response = contract["response"]
    assert len(response.split("\n\n")) == 3
    for phrase in (
        "Trust helps people in a community rely on one another",
        "Think of a shared garden",
        "Stewardship is tending the garden together",
    ):
        assert phrase in response
    assert contract["answer_basis"]["kind"] == "general_knowledge"
    assert contract["answer_basis"]["label"] == "Conceptual explanation"
    assert "not represented as the source" in contract["answer_basis"]["explanation"]
    assert "source_url" not in contract["answer_basis"]


def test_trust_community_stewardship_contract_has_renderer_ready_verified_doorway():
    contract = main._trust_community_stewardship_final_contract(QUERY)
    doorway = contract["recommendation"]
    assert doorway["title"] == (
        "Trust Architecture: The Missing Infrastructure Behind Functional Societies"
    )
    assert doorway["url"] == (
        "https://geralddaquila.com/2026/09/07/"
        "trust-architecture-the-missing-infrastructure-behind-functional-societies/"
    )
    assert doorway["kind"] == "archive_resource"
    assert "source_url" not in contract["answer_basis"]
    assert doorway["rationale"]
    restored = main._guide_restore_verified_doorway(
        {"response": contract["response"], "recommendation": doorway},
        QUERY,
    )
    assert restored["recommendation"]["title"] == doorway["title"]
    assert restored["recommendation"]["url"] == doorway["url"]
    assert restored["recommendation"]["rationale"] == doorway["rationale"]


def test_trust_contract_does_not_capture_unrelated_queries():
    assert main._trust_community_stewardship_final_contract(
        "What is the purpose of reciprocity in a community?"
    ) is None
    assert main._trust_community_stewardship_final_contract(
        "How can I build trust with a friend?"
    ) is None


def test_trust_contract_is_enforced_at_the_final_visitor_boundary():
    source = Path(main.__file__).read_text(encoding="utf-8")
    marker = "_trust_stewardship_contract = _trust_community_stewardship_final_contract(query)"
    contract_index = source.index(marker)
    provenance_index = source.index("# Response provenance metrics", contract_index)
    payload_index = source.index("payload = {", provenance_index)
    assert contract_index < provenance_index < payload_index
    assert "composition_result = None" in source[contract_index:provenance_index]


def test_trust_recovery_is_not_misrepresented_as_archive_evidence():
    from gold_star_evidence_validation import build_evidence_assessment

    contract = main._trust_community_stewardship_final_contract(QUERY)
    refs, assessment = build_evidence_assessment(
        QUERY, contract["response"], contract["answer_basis"], []
    )
    assert refs == []
    assert assessment["status"] == "not_applicable"
    assert assessment["reason"] == "answer_not_attributed_to_archive"


def test_trust_recovery_keeps_related_archive_doorway_separate():
    contract = main._trust_community_stewardship_final_contract(QUERY)
    assert contract["answer_basis"]["kind"] == "general_knowledge"
    assert "source_url" not in contract["answer_basis"]
    assert contract["recommendation"]["kind"] == "archive_resource"
