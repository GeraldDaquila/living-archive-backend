import pytest

from fsd_episode_contract import CONTRACT_VERSION
from fsd_episode_report_contract import FSDEpisodeReportError, validate_episode_report


def episode():
    return {
        "contract_version": CONTRACT_VERSION,
        "scale": "institution",
        "prior_understanding": "clear",
        "experience_type": "observed_outcome",
        "consequence_significance": "material_outcome_or_decision",
        "understanding_after": "revised",
        "reconsideration_basis": "directly_changed_explanation",
        "subsequent_response": "decision_or_action_changed",
        "understanding_action_link": "directly_informed",
        "response_available": "yes",
        "non_change_reason": "not_applicable",
    }


def report():
    return {
        "summary": "The account describes one consequential episode and a subsequent response.",
        "episode_observation": "The respondent reports that an observed outcome led to reconsideration.",
        "strengths": ["The experience was recognized."],
        "enabling_conditions": ["Relevant evidence was available."],
        "constraints": [],
        "next_steps": ["Compare this account with independent records where appropriate."],
        "archive_reference_ids": ["A01"],
    }


def refs():
    return [{
        "reference_id": "A01",
        "title": "Correspondence and Correctability",
        "url": "https://geralddaquila.com/foundational-reference",
    }]


def test_report_separates_respondent_account_from_archive_conceptual_context():
    result = validate_episode_report(report(), episode(), refs())
    assert result["episode_provenance"]["independently_verified"] is False
    assert result["archive_references"][0]["role"] == "conceptual_context_only"
    assert "do not verify" in result["archive_reference_notice"]
    assert result["episode_interpretation"]["overall"] == "both_transitions_reported"
    assert "does not establish stable system capacity" in result["inference_limit"]


def test_archive_references_are_optional_and_not_required_as_episode_evidence():
    candidate = report()
    candidate["archive_reference_ids"] = []
    result = validate_episode_report(candidate, episode(), [])
    assert result["archive_references"] == []


def test_rejects_unknown_or_external_archive_reference():
    with pytest.raises(FSDEpisodeReportError):
        validate_episode_report(report(), episode(), [{
            "reference_id": "A01", "title": "External", "url": "https://example.org/source"
        }])


def test_rejects_report_claiming_archive_verifies_episode():
    candidate = report()
    candidate["episode_observation"] = "The Archive independently verifies the event."
    result = validate_episode_report(candidate, episode(), refs())
    assert result["episode_provenance"]["independently_verified"] is False
    assert "do not verify" in result["archive_reference_notice"]


def test_rejects_internal_reasoning_terms_and_extra_fields():
    candidate = report()
    candidate["summary"] = "SEE MOVE REPEAT"
    with pytest.raises(FSDEpisodeReportError):
        validate_episode_report(candidate, episode(), refs())
    candidate = report()
    candidate["diagnosis"] = "permanent"
    with pytest.raises(FSDEpisodeReportError):
        validate_episode_report(candidate, episode(), refs())


def test_rejects_unbounded_or_invalid_report_lists():
    candidate = report()
    candidate["strengths"] = ["x" * 261]
    with pytest.raises(FSDEpisodeReportError):
        validate_episode_report(candidate, episode(), refs())
