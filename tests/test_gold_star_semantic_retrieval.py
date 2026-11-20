"""Behavioral tests for semantic Gold Star retrieval and abstention."""
import gold_star_lessons as lessons
import gold_star_semantic_retrieval as semantic


def test_semantic_paraphrase_can_retrieve_without_two_word_overlap(monkeypatch):
    target = next(
        item for item in lessons._LESSONS
        if item["id"] == "gs-2026-11-21-transformation-rebranding-structural-change"
    )
    query = "When does organizational change amount to nothing more than rebranding?"
    query_terms = lessons._concept_terms(query)
    assert len(query_terms & target["signature_terms"]) < 2
    monkeypatch.setattr(
        semantic, "rank_semantic_lessons",
        lambda _query, candidates: {item["id"]: (0.86 if item["id"] == target["id"] else 0.20) for item in candidates},
    )
    result = lessons.select_lesson_candidates(query)
    assert result
    assert result[0]["benchmark_id"] == target["id"]
    assert result[0]["exact"] is False


def test_semantic_similarity_without_subject_anchor_is_rejected(monkeypatch):
    monkeypatch.setattr(
        semantic, "rank_semantic_lessons",
        lambda _query, candidates: {item["id"]: 0.91 for item in candidates},
    )
    result = lessons.select_lesson_candidates("How do tides affect coastal ecosystems?")
    assert result == []


def test_close_semantic_candidates_are_withheld_as_ambiguous(monkeypatch):
    candidates = [
        item for item in lessons._LESSONS
        if item["runtime_transfer"]
    ][:2]
    scores = {item["id"]: 0.83 for item in candidates}
    monkeypatch.setattr(
        semantic, "rank_semantic_lessons",
        lambda _query, _candidates: scores,
    )
    # A broad query deliberately shares no subject anchor with either candidate.
    assert lessons.select_lesson_candidates("How should this be understood?") == []
