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

def test_real_bge_decision_rights_paraphrase_and_cross_domain_abstention():
    """Measure the anchorless decision-rights bridge against a cross-domain negative."""
    candidates = _candidates()
    positive_query = "How do decision rights affect institutional responsibility?"
    negative_query = "How should I assign responsibilities when organizing a home garden?"

    target = next(
        item for item in candidates
        if item["id"] == "general-guide-delegated-judgment-moral-limits-gold-star-2026-11-13"
    )
    positive_scores = rank_semantic_lessons(positive_query, candidates)
    negative_scores = rank_semantic_lessons(negative_query, candidates)

    positive_selected = lessons.select_lesson_candidates(positive_query)
    negative_selected = lessons.select_lesson_candidates(negative_query)

    assert positive_scores.get(target["id"], 0.0) >= 0.82, (
        "Real BGE score for the anchorless decision-rights transfer did not "
        f"clear the semantic-only floor: {positive_scores.get(target['id'])}; "
        f"top candidates={sorted(positive_scores.items(), key=lambda row: -row[1])[:5]}"
    )
    assert positive_selected and positive_selected[0]["benchmark_id"] == target["id"], (
        "The real-model decision-rights paraphrase did not recover Gold Star #77: "
        f"selected={[item['benchmark_id'] for item in positive_selected]}"
    )
    assert target["id"] not in [item["benchmark_id"] for item in negative_selected], (
        "A cross-domain gardening query incorrectly activated the delegated-judgment "
        f"Gold Star: selected={[item['benchmark_id'] for item in negative_selected]}, "
        f"target score={negative_scores.get(target['id'])}"
    )
