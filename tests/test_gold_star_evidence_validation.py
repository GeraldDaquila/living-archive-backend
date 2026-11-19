"""Evidence provenance validation tests; lexical signals never certify entailment."""
from gold_star_evidence_validation import build_evidence_assessment, validate_evidence_payload


def _doc(url="https://geralddaquila.com/essays/stewardship/", title="Stewardship", body="Stewardship involves responsibility, care, and accountable action."):
    return {"title": title, "url": url, "text": body}


def test_archive_supported_answer_requires_verified_source_evidence():
    refs, assessment = build_evidence_assessment(
        "What is stewardship?", "Stewardship involves care and responsibility.",
        {"kind": "archive_supported"}, []
    )
    assert refs == []
    assert assessment["status"] == "fail"
    assert assessment["reason"] == "archive_claim_without_verified_evidence"


def test_canonical_source_provenance_passes_but_claim_support_stays_review_required():
    refs, assessment = build_evidence_assessment(
        "What is stewardship?", "Stewardship involves care and responsibility.",
        {"kind": "archive_supported"}, [_doc()]
    )
    payload = {
        "answer_basis": {"kind": "archive_supported"},
        "evidence": refs,
        "evidence_validation": assessment,
    }
    result = validate_evidence_payload("What is stewardship?", payload)
    assert result["status"] == "pass"
    assert result["reference_count"] == 1
    assert result["claim_support"]["status"] == "review_required"
    assert result["semantic_certification"] is False


def test_noncanonical_or_http_sources_are_not_verified_archive_evidence():
    refs, assessment = build_evidence_assessment(
        "What is stewardship?", "Answer text.",
        {"kind": "archive_supported"},
        [_doc(url="http://geralddaquila.com/essay/"), _doc(url="https://example.org/essay/")]
    )
    assert refs == []
    assert assessment["status"] == "fail"


def test_approved_reference_contract_can_support_archive_reference_without_fabricated_url():
    refs, assessment = build_evidence_assessment(
        "Explain the approved Archive reference.", "A bounded explanation.",
        {"kind": "archive_reference"}, [], approved_reference_id="registered-cosmology-recovery-v1"
    )
    assert len(refs) == 1
    assert refs[0]["source_type"] == "approved_reference_contract"
    result = validate_evidence_payload(
        "Explain the approved Archive reference.",
        {"answer_basis": {"kind": "archive_reference"}, "evidence": refs, "evidence_validation": assessment},
    )
    assert result["status"] == "pass"


def test_general_knowledge_and_exact_gold_standards_do_not_require_archive_sources():
    refs, assessment = build_evidence_assessment(
        "What is photosynthesis?", "Photosynthesis converts light energy.",
        {"kind": "general_knowledge"}, []
    )
    assert refs == []
    assert assessment["status"] == "not_applicable"
    assert validate_evidence_payload(
        "What is photosynthesis?", {"answer_basis": {"kind": "general_knowledge"}}
    )["status"] == "not_applicable"
    assert validate_evidence_payload(
        "What is photosynthesis?", {"answer_basis": {"kind": "archive_supported"}},
        exact_standard=True,
    )["status"] == "not_applicable"


def test_archive_claim_rejects_tampered_evidence_digest_and_count():
    refs, assessment = build_evidence_assessment(
        "What is stewardship?", "Stewardship involves care.",
        {"kind": "archive_supported"}, [_doc()]
    )
    refs[0]["content_sha256"] = "tampered"
    payload = {"answer_basis": {"kind": "archive_supported"}, "evidence": refs, "evidence_validation": assessment}
    assert validate_evidence_payload("What is stewardship?", payload)["reason"] == "invalid_evidence_reference"
    refs, assessment = build_evidence_assessment(
        "What is stewardship?", "Stewardship involves care.",
        {"kind": "archive_supported"}, [_doc()]
    )
    assessment["reference_count"] = 0
    payload = {"answer_basis": {"kind": "archive_supported"}, "evidence": refs, "evidence_validation": assessment}
    assert validate_evidence_payload("What is stewardship?", payload)["reason"] == "evidence_reference_count_mismatch"


def test_temporal_queries_are_flagged_for_review_without_inventing_freshness():
    refs, assessment = build_evidence_assessment(
        "What is the latest stewardship guidance today?", "A response.",
        {"kind": "archive_supported"}, [_doc()]
    )
    assert refs
    assert assessment["temporal_validity"]["status"] == "review_required"
    assert assessment["semantic_certification"] is False
