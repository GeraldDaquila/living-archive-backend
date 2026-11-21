"""Regression contracts for Gold Star held-out evaluation isolation."""

import gold_star_heldout_evaluation as evaluation
import gold_star_lessons as lessons


def test_held_out_evaluation_passes_against_approved_transfer_contract(monkeypatch):
    synthetic = {
        "benchmark_id": "general-guide-agency-circumstance-gold-star-2026-11-09",
        "query": "How should responsibility be understood when circumstances constrain choice?",
        "known_theme": "Hold personal agency and limiting circumstances together.",
        "assertions": ["Avoid blame and fatalism."],
        "terms": lessons._tokens("responsibility circumstances constrain choice"),
        "runtime_transfer": True,
        "variants": [
            "How should we understand personal responsibility when circumstances limit people's choices?"
        ],
    }
    monkeypatch.setattr(lessons, "_LESSONS", [synthetic])
    report = evaluation.evaluate()
    assert report["passed"], report


def test_held_out_evaluation_expectations_are_independent_of_live_registry(monkeypatch):
    original_expected = [case["expected_id"] for case in evaluation.HELD_OUT_CASES]
    monkeypatch.setattr(lessons, "_LESSONS", [])
    report = evaluation.evaluate()
    assert [item["expected_id"] for item in report["results"]] == original_expected
    assert report["passed"] is False


def test_pending_fixture_record_cannot_enter_live_transfer_pool():
    assert lessons.select_lesson(
        "How can language about development make some people seem inferior?"
    ) is None


def test_held_out_evaluation_is_not_a_composition_path():
    assert not hasattr(evaluation, "compose")
