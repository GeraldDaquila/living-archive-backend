"""Diagnostic-only real-BGE baseline for the governed decision-rights benchmark.

This records the current selector's candidate set against steward-selected
labels. It intentionally does not assert retrieval quality or change runtime
behavior; misses and false positives are emitted as evidence for review.
"""
import json
from pathlib import Path

import gold_star_lessons as lessons
from gold_star_semantic_retrieval import rank_semantic_lessons

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = json.loads(
    (ROOT / "docs/qa/decision_rights_candidate_set_benchmark.json").read_text(encoding="utf-8")
)


def test_real_bge_candidate_set_baseline():
    rows = []
    for case in BENCHMARK["cases"]:
        selected = lessons.select_lesson_candidates(case["query"], limit=4)
        predicted = [item["benchmark_id"] for item in selected]
        # Counterfactual semantic ranking for every query, including cases where
        # the production selector exits early on a lexical match. This measures
        # whether the lexical short-circuit suppresses potentially useful BGE
        # candidates; it does not alter selector behavior or apply thresholds.
        semantic_ranked = rank_semantic_lessons(case["query"], lessons._LESSONS)
        semantic_top = sorted(
            semantic_ranked.items(), key=lambda pair: (-pair[1], pair[0])
        )[:3]
        expected = (
            case["expected_core"]
            + case["expected_conditional"]
            + case["expected_related_conditional"]
        )
        expected_set = set(expected)
        predicted_set = set(predicted)
        true_positive = len(expected_set & predicted_set)
        false_positive = len(predicted_set - expected_set)
        false_negative = len(expected_set - predicted_set)
        precision = true_positive / len(predicted_set) if predicted_set else (1.0 if not expected_set else 0.0)
        recall = true_positive / len(expected_set) if expected_set else (1.0 if not predicted_set else 0.0)
        rows.append({
            "case_id": case["case_id"],
            "expected": expected,
            "selected": predicted,
            "counterfactual_semantic_top3": [
                {"benchmark_id": benchmark_id, "cosine": round(score, 4)}
                for benchmark_id, score in semantic_top
            ],
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "false_positives": false_positive,
            "false_negatives": false_negative,
            "expected_abstention": case["abstain"],
            "actual_abstention": not bool(predicted),
        })

    print("GOLD_STAR_CANDIDATE_SET_BASELINE=" + json.dumps(rows, sort_keys=True))
    # This is a measurement run, not a quality gate. Its successful completion
    # means the real-model baseline was measured, not that retrieval is adequate.
    assert len(rows) == len(BENCHMARK["cases"])
    assert all(len(row["selected"]) <= 3 for row in rows)
    assert all(len(row["selected"]) == len(set(row["selected"])) for row in rows)
