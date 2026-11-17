"""Regression tests for integrated nonprofit culture/power/care/governance questions."""

import main
import general_guide_composition as composition


QUERY = (
    "A nonprofit's founder is widely trusted, while staff report fear and high turnover. "
    "How can the Guide integrate culture, power, leadership, care, and governance "
    "without diagnosing individuals from limited evidence?"
)


def test_integrated_nonprofit_question_recovers_answer_and_relevant_doorway(monkeypatch):
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda query: None)

    result = main._guide_finalize_visitor_payload(
        {
            "response": "The Guide could not complete this question right now.",
            "recommendation": {
                "title": "Philippine Systems, Society, and Culture",
                "url": "https://geralddaquila.com/philippine-systems/",
            },
        },
        QUERY,
    )

    answer = result["response"]
    assert composition._has_nonprofit_culture_power_care_governance_explanation(answer)
    assert answer.startswith("A founder can be widely trusted")
    assert "different positions of dependence, access, and power" in answer
    assert "Care asks whether workloads, safety, dignity" in answer
    assert "Governance asks whether people have safe ways" in answer
    assert "they do not prove an individual's motives" in answer
    assert result.get("answer", answer) == answer
    assert result["recommendation"]["title"] == "Building Trust-Centered Organizations"
    assert result["recommendation"]["url"] == (
        "https://geralddaquila.com/2026/09/07/building-trust-centered-organizations/"
    )
    assert result["canonical_doorway"] == result["recommendation"]
    assert result["doorway_rationale"]
    assert result["processing"] == (
        "final_visitor_boundary_nonprofit_culture_power_care_governance"
    )


def test_integrated_nonprofit_question_matches_case_and_whitespace_variants():
    variant = (
        "  A NONPROFIT'S FOUNDER IS WIDELY TRUSTED, WHILE STAFF REPORT FEAR AND HIGH TURNOVER. "
        "How can the Guide integrate culture, power, leadership, care, and governance "
        "without diagnosing individuals from limited evidence?  "
    )
    assert composition._requires_nonprofit_culture_power_care_governance(variant)


def test_integrated_nonprofit_question_does_not_capture_generic_leadership_questions():
    adjacent = (
        "How can a nonprofit improve leadership and governance while building a healthy culture?"
    )
    assert not composition._requires_nonprofit_culture_power_care_governance(adjacent)


def test_integrated_nonprofit_answer_contract_rejects_generic_failure_copy():
    assert not composition._has_nonprofit_culture_power_care_governance_explanation(
        "The Guide could not complete this question right now."
    )


def test_integrated_nonprofit_recovery_is_three_part_and_non_diagnostic():
    answer = composition._nonprofit_culture_power_care_governance_recovery()
    assert composition._has_nonprofit_culture_power_care_governance_explanation(answer)
    assert "does not, by itself, establish why any individual acted" in answer
    assert "public trust does not disprove staff harm" in answer
