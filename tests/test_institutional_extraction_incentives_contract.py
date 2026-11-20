from pathlib import Path

from institutional_extraction_incentives_contract import (
    canonical_doorway,
    is_institutional_extraction_incentives_question,
    recovery_response,
)


def test_recognizes_leadership_question_about_institutional_extraction_rewards():
    assert is_institutional_extraction_incentives_question(
        "How should a leader respond when institutional incentives reward short-term extraction?"
    )


def test_recognizes_close_paraphrase_without_overmatching_generic_incentives():
    assert is_institutional_extraction_incentives_question(
        "What should an executive do when organizational targets reward depletion for immediate returns?"
    )
    assert not is_institutional_extraction_incentives_question(
        "How do incentives influence individual choices?"
    )
    assert not is_institutional_extraction_incentives_question(
        "What is institutional extraction?"
    )


def test_recovery_addresses_incentive_redesign_and_accountability():
    answer = recovery_response().casefold()
    for term in (
        "incentive-design problem",
        "who captures the gains",
        "who carries the delayed costs",
        "authority",
        "protect dissent",
        "pilot",
        "baseline",
        "board",
        "circulation and renewal",
    ):
        assert term in answer


def test_doorway_is_the_verified_regenerative_governance_essay():
    doorway = canonical_doorway()
    assert doorway["title"] == (
        "Regenerative Governance: What Comes After Extraction-Based Systems?"
    )
    assert doorway["url"] == (
        "https://geralddaquila.com/2026/06/08/"
        "regenerative-governance-what-comes-after-extraction-based-systems/"
    )
    assert "direct continuation" in doorway["rationale"]


def test_main_runtime_wires_the_contract_at_selection_and_final_boundary():
    root = Path(__file__).resolve().parents[1]
    main_source = (root / "main.py").read_text(encoding="utf-8")
    assert "is_institutional_extraction_incentives_question" in main_source
    assert '"institutional_extraction_incentives"' in main_source
    assert "institutional_extraction_incentives_final_boundary" in main_source
