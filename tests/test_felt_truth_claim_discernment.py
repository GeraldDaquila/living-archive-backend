"""Final-boundary acceptance for felt-truth claim discernment."""

import pytest

import deterministic_answer_recovery as recovery


QUERY = (
    "What claims am I accepting because they feel true, beautiful, or "
    "empowering—and what would it take to examine them carefully?"
)


def test_live_question_is_classified_as_felt_truth_discernment():
    assert recovery.is_felt_truth_claim_discernment_question(QUERY)


def test_related_paraphrase_uses_the_same_discernment_family():
    assert recovery.is_felt_truth_claim_discernment_question(
        "Which beliefs feel empowering or beautiful, and how can I test the evidence behind them?"
    )


@pytest.mark.parametrize(
    "query",
    [
        "What is the most beautiful place to visit in Manila?",
        "How can I make an empowering presentation?",
        "What claims did the court accept as evidence?",
    ],
)
def test_unrelated_questions_do_not_enter_the_felt_truth_family(query):
    assert not recovery.is_felt_truth_claim_discernment_question(query)


def test_recovery_covers_claim_evidence_disconfirmation_and_meaning():
    answer = recovery.compose_recovery(QUERY)
    folded = answer.casefold()
    for required in (
        "state the claim precisely",
        "separate experience from interpretation",
        "independently corroborated",
        "disconfirming evidence",
        "alternative explanations",
        "open to correction",
        "personal significance",
    ):
        assert required in folded


def test_registered_doorway_is_the_verified_patterns_essay():
    doorway = recovery.registered_recovery_recommendation(QUERY)
    assert doorway["title"] == "Seeing Patterns Without Fooling Yourself"
    assert doorway["url"] == (
        "https://geralddaquila.com/2026/04/06/seeing-patterns-without-fooling-yourself/"
    )
    assert "not independent proof" in doorway["rationale"]


def test_final_visitor_boundary_overrides_provider_or_generic_recovery_output():
    pytest.importorskip("fastapi")
    import main

    for query in (
        QUERY,
        "Which beliefs feel empowering or beautiful, and how can I test the evidence behind them?",
    ):
        result = main._guide_finalize_visitor_payload(
            {
                "ok": True,
                "response": (
                    "The Archive material available here offers this starting point: "
                    "After Awakening: How Your True Purpose Begins to Reveal Itself. "
                    "I did not identify a directly relevant Archive resource to recommend."
                ),
                "recommendation": None,
            },
            query,
        )
        assert result["processing"] == (
            "final_visitor_boundary_felt_truth_claim_discernment"
        )
        assert "seven steps" in result["response"].casefold()
        assert result["recommendation"]["title"] == (
            "Seeing Patterns Without Fooling Yourself"
        )
        assert result["recommendation"]["url"] == (
            "https://geralddaquila.com/2026/04/06/seeing-patterns-without-fooling-yourself/"
        )
        assert result["answer_basis"]["kind"] == "general_knowledge"
        assert "not independent proof" in result["answer_basis"]["explanation"]


def test_final_visitor_boundary_does_not_capture_unrelated_queries():
    pytest.importorskip("fastapi")
    import main

    result = main._guide_finalize_visitor_payload(
        {"ok": True, "response": "A concise answer."},
        "What is the most beautiful place to visit in Manila?",
    )
    assert result.get("processing") != (
        "final_visitor_boundary_felt_truth_claim_discernment"
    )


def test_felt_truth_candidate_is_not_promoted_into_the_gold_star_ledger_early():
    from pathlib import Path
    import json

    root = Path(recovery.__file__).resolve().parent
    registry = json.loads(
        (root / "docs" / "qa" / "gold_standard_registry.json").read_text(
            encoding="utf-8"
        )
    )
    assert not any(
        item.get("benchmark_id") == "gs-2026-11-19-felt-truth-claim-discernment"
        for item in registry["records"]
    )
