import pytest

from fsd_report_contract import (
    FSDReportContractError,
    validate_fsd_report,
)


EVIDENCE = [
    {"evidence_id": "E01", "quantum_id": "Q001_CORRESPONDENCE", "title": "Canonical source one", "url": "https://geralddaquila.com/source-one"},
    {"evidence_id": "E02", "quantum_id": "Q002_CORRECTABILITY", "title": "Canonical source two", "url": "https://geralddaquila.com/source-two"},
]


def valid_report():
    return {
        "summary": "A bounded synthesis supported by the available sources.",
        "recurring_condition": "A recurring gap between information and corrective authority.",
        "reported_signal": "The selected scale reports difficulty correcting the condition.",
        "strengths": ["The issue can be recognized."],
        "enabling_conditions": ["Relevant information is available."],
        "constraints": ["Corrective authority is unclear."],
        "next_steps": ["Examine one concrete decision and its consequences."],
        "evidence_ids": ["E01", "E02"],
    }


def test_report_binds_exact_server_evidence_and_marks_other_scales_unassessed():
    result = validate_fsd_report(valid_report(), EVIDENCE, "organization")
    assert result["evidence"] == EVIDENCE
    assert result["scope"]["organization"] == "reported_signal"
    assert result["scope"]["self"] == "not_assessed"
    assert result["scope"]["relationships"] == "not_assessed"
    assert result["scope"]["state"] == "not_assessed"
    assert result["scope"]["civilization"] == "not_assessed"


def test_rejects_unapproved_fields():
    report = valid_report()
    report["diagnosis"] = "browser-supplied"
    with pytest.raises(FSDReportContractError):
        validate_fsd_report(report, EVIDENCE, "self")


def test_rejects_unknown_evidence_ids():
    report = valid_report()
    report["evidence_ids"] = ["E01", "EVIL"]
    with pytest.raises(FSDReportContractError):
        validate_fsd_report(report, EVIDENCE, "self")


def test_rejects_internal_reasoning_vocabulary():
    report = valid_report()
    report["summary"] = "SEE then MOVE then REPEAT."
    with pytest.raises(FSDReportContractError):
        validate_fsd_report(report, EVIDENCE, "self")


def test_rejects_insufficient_independent_evidence():
    with pytest.raises(FSDReportContractError):
        validate_fsd_report(valid_report(), EVIDENCE[:1], "self")


def test_rejects_invalid_scale_as_no_cross_scale_authority():
    with pytest.raises(FSDReportContractError):
        validate_fsd_report(valid_report(), EVIDENCE, "everywhere")


def test_missing_scale_does_not_claim_a_scale_specific_signal():
    result = validate_fsd_report(valid_report(), EVIDENCE, None)
    assert result["reported_signal"] == (
        "No diagnostic scale was selected; no scale-specific signal is assessed."
    )
    assert set(result["scope"].values()) == {"not_assessed"}
