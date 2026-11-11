import gold_star_lessons as lessons
from gold_star_heldout_evaluation import evaluate

def test_held_out_evaluation_passes_against_approved_transfer_contract(monkeypatch):
    # Held-out evaluation uses a synthetic approved lesson rather than relaxing
    # the production registry's current approval state.
    monkeypatch.setattr(lessons, "_LESSONS", [{
        "id": "general-guide-agency-circumstance-gold-star-2026-11-09",
        "query": "How should responsibility be understood when circumstances constrain choice?",
        "known_theme": "Hold personal agency and limiting circumstances together.",
        "assertions": ["Avoid blame and fatalism."],
        "terms": lessons._tokens("responsibility circumstances constrain choice"),
        "runtime_transfer": True,
        "variants": [
            "How should we understand personal responsibility when circumstances limit people's choices?"
        ],
    }])
    report = evaluate()
    assert report["passed"], report

def test_pending_fixture_record_cannot_enter_live_transfer_pool():
    # The registry may contain promising future candidates. Until their status is
    # explicitly promoted, production learning must abstain.
    assert lessons.select_lesson(
        "How can language about development make some people seem inferior?"
    ) is None

def test_held_out_evaluation_is_not_a_composition_path():
    assert not hasattr(__import__("gold_star_heldout_evaluation"), "compose")
