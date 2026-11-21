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


def test_pending_fixture_record_cannot_enter_live_transfer_pool():
    # This is an existing unresolved selector behavior test, kept independent of
    # the synthetic fixture above so it continues to expose any false-positive.
    assert lessons.select_lesson(
        "How can language about development make some people seem inferior?"
    ) is None


def test_held_out_evaluation_is_not_a_composition_path():
    assert not hasattr(__import__("gold_star_heldout_evaluation"), "compose")
