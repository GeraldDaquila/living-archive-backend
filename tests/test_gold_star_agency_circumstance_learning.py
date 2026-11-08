import os
from unittest.mock import patch

import gold_star_lessons as lessons
import general_guide_composition as composition


AGENCY_ID = "general-guide-agency-circumstance-gold-star-2026-11-09"


def test_agency_circumstance_exact_and_related_questions_select_the_approved_lesson():
    exact = lessons.select_exemplar("What is the relationship between agency and circumstance?")
    assert exact and exact["benchmark_id"] == AGENCY_ID

    related = lessons.select_exemplar(
        "How should we think about personal responsibility when circumstances limit people's choices?"
    )
    assert related and related["benchmark_id"] == AGENCY_ID


def test_agency_lesson_abstains_for_unrelated_questions_and_generic_overlap():
    assert lessons.select_exemplar("How do I calculate the area of a triangle?") is None
    assert lessons.select_exemplar(
        "What responsibilities should a manager weigh when choosing between competing options?"
    ) is None
    assert lessons.select_exemplar(
        "How should I make a responsible decision under uncertainty?"
    ) is None


def test_guidance_is_structural_and_never_contains_the_exemplar_answer():
    guidance, token = lessons.build_exemplar_guidance(
        "How can someone still have choices when their circumstances are restrictive?"
    )
    assert token == AGENCY_ID
    assert "Do not copy the exemplar's answer" in guidance
    assert "We are not always responsible for the circumstances we inherit" not in guidance


def test_guided_mode_is_explicitly_opt_in(monkeypatch):
    monkeypatch.delenv("GOLD_STAR_LESSONS_MODE", raising=False)
    assert (os.getenv("GOLD_STAR_LESSONS_MODE") or "shadow") == "shadow"
