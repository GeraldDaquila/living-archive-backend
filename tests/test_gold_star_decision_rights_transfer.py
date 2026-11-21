"""Regression reproduction for Gold Star paraphrase conversion.

The visitor asks about decision rights and institutional responsibility.
Gold Star #77 concerns delegated judgment and institutional accountability.
A strong semantic match should be considered even when unrelated lexical
matches exist; lexical matches must not suppress semantic recovery.
"""
import gold_star_lessons as lessons
import gold_star_semantic_retrieval as semantic


QUESTION = "How do decision rights affect institutional responsibility?"
TARGET = "general-guide-delegated-judgment-moral-limits-gold-star-2026-11-13"


def test_decision_rights_question_recovers_delegated_judgment_gold_star(monkeypatch):
    target = next(item for item in lessons._LESSONS if item["id"] == TARGET)
    query_terms = lessons._concept_terms(QUESTION)
    # Current subject signature does not contain a two-term lexical anchor.
    assert len(query_terms & target["signature_terms"]) < 2

    calls = []

    def ranked(_query, candidates):
        calls.append([item["id"] for item in candidates])
        return {
            item["id"]: (0.90 if item["id"] == TARGET else 0.20)
            for item in candidates
        }

    monkeypatch.setattr(semantic, "rank_semantic_lessons", ranked)
    selected = lessons.select_lesson_candidates(QUESTION)

    # This is the desired behavior: strong conceptual evidence must be able
    # to supplement misleading lexical candidates rather than being skipped.
    assert calls, "semantic retrieval was suppressed by unrelated lexical matches"
    assert selected
    assert selected[0]["benchmark_id"] == TARGET
    assert selected[0]["exact"] is False


def test_active_contribution_exposes_decision_rights_gold_star_to_composition(monkeypatch):
    monkeypatch.setattr(
        semantic,
        "rank_semantic_lessons",
        lambda _query, candidates: {
            item["id"]: (0.90 if item["id"] == TARGET else 0.20)
            for item in candidates
        },
    )
    contribution = lessons.active_quality_contribution(QUESTION)
    assert contribution
    assert contribution["benchmark_id"] == TARGET
    assert contribution["authority_mode"] == "structural_guidance_only"
    assert "delegation" in contribution["discipline"].lower()
