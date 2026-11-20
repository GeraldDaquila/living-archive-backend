"""Real-model integration checks for the canonical BGE Gold Star retriever.

These tests deliberately do not mock embeddings. They validate the deployed
384-dimensional model, a held-out paraphrase, and a near-domain distractor.
"""
import gold_star_lessons as lessons
from gold_star_semantic_retrieval import rank_semantic_lessons

TARGET = "gs-2026-11-21-transformation-rebranding-structural-change"


def _candidates():
    return [item for item in lessons._LESSONS if item["runtime_transfer"]]


def test_real_bge_separates_held_out_paraphrase_from_near_domain_distractor():
    candidates = _candidates()
    positive_query = "When does institutional change amount to mere rebranding?"
    distractor_query = "How should I rebrand my garden?"

    positive_score = rank_semantic_lessons(positive_query, candidates)[TARGET]
    distractor_score = rank_semantic_lessons(distractor_query, candidates)[TARGET]

    # Calibrated against the actual model: the held-out structural question
    # must clear the threshold while the garden-branding distractor must not.
    assert positive_score >= 0.65
    assert distractor_score < 0.65

    selected = lessons.select_lesson_candidates(positive_query)
    assert selected
    assert selected[0]["benchmark_id"] == TARGET
    assert selected[0]["exact"] is False

    assert lessons.select_lesson_candidates(distractor_query) == []
