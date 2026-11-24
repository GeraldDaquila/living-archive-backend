import gold_star_lessons as lessons
from gold_star_heldout_evaluation import evaluate


def _synthetic_lesson():
    # Match the selector's actual internal lesson schema. This fixture is a
    # controlled test double; it does not alter registry approval or authority.
    query = "How should responsibility be understood when circumstances constrain choice?"
    variants = [
        "How should we understand personal responsibility when circumstances limit people's choices?"
    ]
    return {
        "id": "general-guide-agency-circumstance-gold-star-2026-11-09",
        "query": query,
        "known_theme": "Hold personal agency and limiting circumstances together.",
        "assertions": ["Avoid blame and fatalism."],
        "terms": lessons._tokens("responsibility circumstances constrain choice"),
        "signature_terms": lessons._concept_terms(" ".join((
            query,
            "Hold personal agency and limiting circumstances together.",
            "agency_circumstance_responsibility",
            " ".join(variants),
        ))),
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
    report = evaluate()
    assert report["passed"], report


def test_user_approved_developmental_language_gold_star_supports_related_transfer():
    # This canonical record is user-approved, explicitly elevated, and active
    # for cross-question quality contribution. A close paraphrase should retrieve
    # structural guidance, not exact-answer authority.
    selected = lessons.select_lesson(
        "How can developmental language become dismissive or hierarchical?"
    )
    assert selected is not None
    assert selected["benchmark_id"] == "general-guide-developmental-language-gold-star-2026-11-09"
    assert selected["runtime_transfer"] is True
    assert selected["exact"] is False


def test_held_out_evaluation_is_not_a_composition_path():
    assert not hasattr(__import__("gold_star_heldout_evaluation"), "compose")


def test_public_commons_gold_star_transfers_to_unseen_civic_renewal_question():
    query = "How should public commons and shared civic infrastructure be stewarded to renew public life?"
    candidates = lessons.select_lesson_candidates(query, limit=4)
    selected = next(
        (item for item in candidates
         if item["benchmark_id"] == "general-guide-public-commons-civic-renewal-2026-11-24"),
        None,
    )
    assert selected is not None, candidates
    assert selected["exact"] is False
    assert selected["runtime_transfer"] is True


def test_public_commons_gold_star_does_not_capture_unrelated_public_service_question():
    query = "How should public library opening hours be scheduled?"
    selected = lessons.select_lesson(query)
    assert selected is None


def test_public_commons_gold_star_contributes_discipline_not_exemplar_answer():
    query = "How should public commons and shared civic infrastructure be stewarded to renew public life?"
    contribution = lessons.active_quality_contribution(query)
    assert contribution is not None
    candidate = next(
        (item for item in contribution["candidates"]
         if item["benchmark_id"] == "general-guide-public-commons-civic-renewal-2026-11-24"),
        None,
    )
    assert candidate is not None, contribution
    assert candidate["discipline"]
    assert candidate["abstention_boundary"]
    assert "expected_response" not in candidate
    assert "expected_response" not in contribution
