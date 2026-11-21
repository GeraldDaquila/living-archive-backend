"""Regression contracts for Gold Star held-out evaluation isolation."""

import gold_star_heldout_evaluation as evaluation
import gold_star_lessons as lessons


def _synthetic_lesson():
    # Match the selector's actual internal lesson schema, including its ID key
    # and precomputed lexical signature fields.
    query = "How should responsibility be understood when circumstances constrain choice?"
    variants = [
        "How should we understand personal responsibility when circumstances limit people's choices?"
    ]
    signature_terms = lessons._concept_terms(" ".join((
        query, "Hold personal agency and limiting circumstances together.",
        "agency_circumstance_responsibility", " ".join(variants),
    )))
    return {
        "id": "general-guide-agency-circumstance-gold-star-2026-11-09",
        "benchmark_id": "general-guide-agency-circumstance-gold-star-2026-11-09",
        "query": query,
        "known_theme": "Hold personal agency and limiting circumstances together.",
        "assertions": ["Avoid blame and fatalism."],
        "terms": lessons._tokens("responsibility circumstances constrain choice"),
        "signature_terms": signature_terms,
        "variant_terms": lessons._concept_terms(" ".join(variants)),
        "reasoning_terms": lessons._concept_terms("agency circumstance responsibility"),
        "runtime_transfer": True,
        "variants": variants,
        "transferable_discipline": "Hold personal agency and limiting circumstances together.",
        "abstention_boundary": "Do not blame or infer beyond evidence.",
        "reasoning_family": "agency_circumstance_responsibility",
    }


def test_held_out_evaluation_passes_against_approved_transfer_contract(monkeypatch):
    monkeypatch.setattr(lessons, "_LESSONS", [_synthetic_lesson()])
    # This test evaluates the positive case explicitly; the other frozen
    # expectations are tested separately against the production selector below.
    case = next(c for c in evaluation.HELD_OUT_CASES if c["expected_id"])
    report = evaluation.evaluate([case])
    assert report["passed"], report


def test_held_out_evaluation_expectations_are_independent_of_live_registry(monkeypatch):
    original_expected = [case["expected_id"] for case in evaluation.HELD_OUT_CASES]
    monkeypatch.setattr(lessons, "_LESSONS", [])
    report = evaluation.evaluate()
    assert [item["expected_id"] for item in report["results"]] == original_expected
    assert report["passed"] is False


def test_pending_fixture_record_cannot_enter_live_transfer_pool():
    # Evaluate against the real, unpatched registry: candidate status is not
    # sufficient for inclusion in the approved structural-learning pool.
    assert lessons.select_lesson(
        "How can language about development make some people seem inferior?"
    ) is None


def test_held_out_evaluation_is_not_a_composition_path():
    assert not hasattr(evaluation, "compose")
