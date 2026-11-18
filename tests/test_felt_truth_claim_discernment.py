"""Browser-facing and runtime acceptance for felt-truth claim discernment."""
import json
from pathlib import Path

import deterministic_answer_recovery as recovery


QUERY = "What claims am I accepting because they feel true, beautiful, or empowering—and what would it take to examine them carefully?"
ROOT = Path(__file__).resolve().parents[1]


def test_live_question_is_classified_as_felt_truth_discernment():
    assert recovery.is_felt_truth_claim_discernment_question(QUERY)


def test_related_paraphrase_uses_same_discernment_family():
    assert recovery.is_felt_truth_claim_discernment_question(
        "Which beliefs feel empowering or beautiful, and how can I test the evidence behind them?"
    )


def test_unrelated_question_does_not_enter_felt_truth_family():
    assert not recovery.is_felt_truth_claim_discernment_question(
        "What is the most beautiful place to visit in Manila?"
    )


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


def test_question_is_registered_as_a_user_approved_gold_star_and_transfer_lesson():
    registry = json.loads((ROOT / "docs/qa/gold_standard_registry.json").read_text())
    reviews = json.loads((ROOT / "docs/qa/gold_star_qualitative_transfer_review.json").read_text())
    record = next(x for x in registry["records"] if x["benchmark_id"] == "gs-2026-11-19-felt-truth-claim-discernment")
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == QUERY
    assert record["runtime_transfer"] is True
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["gold_star_capabilities"]["exact_answer_authority"] is True
    assert record["expected_doorway"]["title"] == "Seeing Patterns Without Fooling Yourself"
    review = next(x for x in reviews["entries"] if x["benchmark_id"] == record["benchmark_id"])
    assert review["activation"] == "active_quality_contributor"
    assert "Do not impose a spiritual framework" in record["transfer_boundary"]


def test_final_visitor_boundary_overrides_provider_output_for_this_task():
    import main

    paraphrase = "Which beliefs feel empowering or beautiful, and how can I test the evidence behind them?"
    result = main._guide_finalize_visitor_payload(
        {"ok": True, "response": "After Awakening is a good starting point.", "recommendation": None},
        paraphrase,
    )
    assert result["processing"] == "final_visitor_boundary_felt_truth_claim_discernment"
    assert "seven steps" in result["response"]
    assert result["recommendation"]["title"] == "Seeing Patterns Without Fooling Yourself"
    assert result["answer_basis"]["kind"] == "general_knowledge"


def test_exact_gold_star_answer_is_terminal_and_uses_its_approved_doorway():
    import main
    from general_guide_gold_standards import resolve_exact_gold_standard

    standard = resolve_exact_gold_standard(QUERY)
    assert standard is not None
    result = main._guide_finalize_visitor_payload(
        {"ok": True, "response": "After Awakening is a good starting point.", "recommendation": None},
        QUERY,
    )
    assert result["processing"] == "final_visitor_boundary_exact_gold_standard"
    assert result["response"] == standard["expected_response"]
    assert result["recommendation"]["title"] == "Seeing Patterns Without Fooling Yourself"

def test_qa_browser_route_is_registered_and_posts_to_real_visitor_endpoint():
    import main

    paths = {getattr(route, "path", None) for route in main.app.routes}
    assert "/qa-browser" in paths
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert 'fetch("/api/query"' in source
    assert 'JSON.stringify({query})' in source
