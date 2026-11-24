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
        "How can language about development make some people seem inferior?"
    )
    assert selected is not None
    assert selected["benchmark_id"] == "general-guide-developmental-language-gold-star-2026-11-09"
    assert selected["runtime_transfer"] is True
    assert selected["exact"] is False


def test_held_out_evaluation_is_not_a_composition_path():
    assert not hasattr(__import__("gold_star_heldout_evaluation"), "compose")


def test_public_commons_gold_star_transfers_to_unseen_civic_renewal_question():
    query = "How can public shared spaces strengthen civic participation and community renewal?"
    selected = lessons.select_lesson(query)
    assert selected is not None
    assert selected["benchmark_id"] == "general-guide-public-commons-civic-renewal-2026-11-24"
    assert selected["exact"] is False
    assert selected["runtime_transfer"] is True
    assert selected["authority_mode"] == "structural_guidance_only"


def test_public_commons_gold_star_does_not_capture_unrelated_public_service_question():
    query = "How should public library opening hours be scheduled?"
    selected = lessons.select_lesson(query)
    assert selected is None


def test_public_commons_gold_star_contributes_discipline_not_exemplar_answer():
    query = "How can public shared spaces strengthen civic participation and community renewal?"
    contribution = lessons.active_quality_contribution(query)
    assert contribution is not None
    assert contribution["benchmark_id"] == "general-guide-public-commons-civic-renewal-2026-11-24"
    assert contribution["authority_mode"] == "structural_guidance_only"
    assert "discipline" in contribution and contribution["discipline"]
    assert "abstention_boundary" in contribution and contribution["abstention_boundary"]
    assert "expected_response" not in contribution
