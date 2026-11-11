import gold_star_lessons as lessons

def test_only_explicitly_approved_records_are_loaded():
    assert lessons._LESSONS
    assert lessons._ALLOWED_STATUSES == frozenset({"USER_APPROVED_GOLD_STANDARD"})

def test_exact_question_is_observable_but_not_automatically_transferable():
    result = lessons.select_lesson("What is institutional memory, and why does it matter?")
    assert result and result["exact"] is True
    assert result["runtime_transfer"] is False

def test_explicit_transfer_matches_related_variant():
    result = lessons.select_lesson(
        "How should we understand personal responsibility when circumstances limit people's choices?"
    )
    assert result
    assert result["benchmark_id"] == "general-guide-agency-circumstance-gold-star-2026-11-09"
    assert result["exact"] is False

def test_unrelated_question_abstains():
    assert lessons.select_lesson("How do I calculate the area of a triangle?") is None

def test_reconstructed_records_cannot_influence_live_learning():
    assert "USER_CONFIRMED_RECONSTRUCTION_NOT_HISTORICAL_EXACT" not in lessons._ALLOWED_STATUSES
