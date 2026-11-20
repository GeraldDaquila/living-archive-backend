"""Real-model integration checks for the canonical BGE Gold Star retriever.

These tests deliberately do not mock embeddings. They validate the deployed
384-dimensional model, one held-out paraphrase, and a near-domain distractor.
"""
import gold_star_lessons as lessons
from gold_star_semantic_retrieval import rank_semantic_lessons

TARGET = "gs-2026-11-21-transformation-rebranding-structural-change"


def _candidates():
    return [item for item in lessons._LESSONS if item["runtime_transfer"]]


def test_real_bge_recovers_held_out_transformation_rebranding_paraphrase():
    query = "When is renewal just cosmetic rebranding?"
    candidates = _candidates()
    scores = rank_semantic_lessons(query, candidates)
    target_score = scores[TARGET]

    # Verify the actual model output, not a mocked ranking.
    assert target_score >= 0.48
    selected = lessons.select_lesson_candidates(query)
    assert selected
    assert selected[0]["benchmark_id"] == TARGET
    assert selected[0]["exact"] is False


def test_real_bge_does_not_transfer_rebranding_lesson_to_garden_branding():
    query = "How should I rebrand my garden?"
    selected = lessons.select_lesson_candidates(query)
    assert not selected or selected[0]["benchmark_id"] != TARGET
