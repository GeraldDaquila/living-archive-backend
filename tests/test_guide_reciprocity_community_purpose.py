"""Final visitor contract for reciprocity's purpose in a community."""

from pathlib import Path
import json

import main

QUERY = "What is the purpose of reciprocity in a community?"
DOORWAY_TITLE = "Reciprocity Before Bureaucracy: How Communities Coordinated Without Modern Institutions"
DOORWAY_URL = (
    "https://geralddaquila.com/2026/06/01/"
    "reciprocity-before-bureaucracy-how-communities-coordinated-without-modern-institutions/"
)


def test_reciprocity_answer_is_substantive_three_paragraph_and_preserves_ethical_boundary():
    contract = main._reciprocity_community_final_contract(QUERY)
    assert contract is not None
    answer = contract["response"]
    assert len(answer.split("\n\n")) == 3
    for phrase in (
        "people support one another over time",
        "not mean keeping score",
        "Think of neighbors taking turns checking on an older resident",
        "receive help later",
        "demand access, obedience, or repayment",
        "kindness becomes a debt ledger",
    ):
        assert phrase in answer


def test_reciprocity_contract_has_general_knowledge_provenance_and_separate_doorway():
    contract = main._reciprocity_community_final_contract(QUERY)
    assert contract["answer_basis"]["kind"] == "general_knowledge"
    assert contract["answer_basis"]["label"] == "Conceptual explanation"
    assert "not represented as the source" in contract["answer_basis"]["explanation"]
    assert "source_url" not in contract["answer_basis"]
    doorway = contract["recommendation"]
    assert doorway["title"] == DOORWAY_TITLE
    assert doorway["url"] == DOORWAY_URL
    assert doorway["kind"] == "archive_resource"
    assert "shared risk" in doorway["rationale"]
    restored = main._guide_restore_verified_doorway(
        {"response": contract["response"], "recommendation": doorway}, QUERY
    )
    assert restored["recommendation"]["title"] == DOORWAY_TITLE
    assert restored["recommendation"]["url"] == DOORWAY_URL


def test_reciprocity_contract_does_not_capture_trust_or_stewardship_queries():
    for query in (
        "What is the role of trust in community stewardship?",
        "How can I build trust in a community?",
        "What is stewardship in a community?",
    ):
        assert main._reciprocity_community_final_contract(query) is None
    assert main._trust_community_stewardship_final_contract(QUERY) is None


def test_reciprocity_contract_accepts_bounded_paraphrases_without_capturing_other_topics():
    for query in (
        "What role does reciprocity play in communities?",
        "Why is reciprocity important in a community?",
        "What does reciprocal support mean in a community?",
    ):
        assert main._is_reciprocity_community_purpose_question(query)
    for query in (
        "What is reciprocity?",
        "What is the purpose of trust in a community?",
        "What is the purpose of reciprocity in stewardship?",
    ):
        assert not main._is_reciprocity_community_purpose_question(query)


def test_reciprocity_contract_is_enforced_at_final_visitor_boundary_before_provenance_and_payload():
    source = Path(main.__file__).read_text(encoding="utf-8")
    marker = "_reciprocity_community_contract = _reciprocity_community_final_contract(query)"
    contract_index = source.index(marker)
    trust_index = source.index(
        "_trust_stewardship_contract = _trust_community_stewardship_final_contract(query)",
        contract_index,
    )
    provenance_index = source.index("# Response provenance metrics", contract_index)
    payload_index = source.index("payload = {", provenance_index)
    block = source[contract_index:trust_index]
    assert contract_index < trust_index < provenance_index < payload_index
    assert "composition_result = {}" in block
    assert "composition_result = None" not in block
    assert 'answer_basis = dict(_reciprocity_community_contract["answer_basis"])' in block
    assert "_normalize_authoritative_recommendation(" in block
    assert '"bounded_reciprocity_community_recovery"' in block


def test_reciprocity_answer_is_not_misrepresented_as_archive_evidence():
    from gold_star_evidence_validation import build_evidence_assessment

    contract = main._reciprocity_community_final_contract(QUERY)
    refs, assessment = build_evidence_assessment(
        QUERY, contract["response"], contract["answer_basis"], []
    )
    assert refs == []
    assert assessment["status"] == "not_applicable"
    assert assessment["reason"] == "answer_not_attributed_to_archive"


def test_reciprocity_registry_candidate_records_verified_doorway_without_freezing_answer():
    registry = json.loads(
        (Path(main.__file__).resolve().parent / "docs/qa/gold_standard_registry.json").read_text(
            encoding="utf-8"
        )
    )
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-reciprocity-community-2026-10-24"
    )
    assert record["status"] == "CANDIDATE"
    assert record["expected_doorway"]["title"] == DOORWAY_TITLE
    assert record["expected_doorway"]["url"] == DOORWAY_URL
    assert record["rating"] is None
    assert "user review" in record["provenance"]["approval_evidence"].lower()
    frozen_reference = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-reciprocity-gold-standard-2026-10-19"
    )
    assert frozen_reference["status"] == "FROZEN_REFERENCE_ONLY"
