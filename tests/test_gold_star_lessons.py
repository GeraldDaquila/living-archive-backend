import gold_star_lessons as lessons


def test_only_explicitly_approved_records_are_loaded():
    assert lessons._LESSONS
    assert lessons._ALLOWED_STATUSES == frozenset({"USER_APPROVED_GOLD_STANDARD"})


def test_exact_question_is_observable_but_not_automatically_transferable():
    result = lessons.select_lesson("What is institutional memory, and why does it matter?")
    assert result and result["exact"] is True
    assert result["runtime_transfer"] is False


def test_explicit_transfer_matches_canonical_structure_agency_lesson():
    result = lessons.select_lesson(
        "How do local choices relate to wider institutional and social circumstances?"
    )
    assert result
    assert result["benchmark_id"] == "gs-2026-11-13-03-cross-scale-orientation-canonical-continuation"
    assert result["exact"] is False


def test_approved_gold_star_with_non_general_subsystem_is_loaded():
    matching = [
        record for record in lessons._LESSONS
        if record["id"] == "gs-2026-11-13-03-cross-scale-orientation-canonical-continuation"
    ]
    assert len(matching) == 1
    assert matching[0]["runtime_transfer"] is True


def test_unrelated_question_abstains():
    assert lessons.select_lesson("How do I calculate the area of a triangle?") is None


def test_reconstructed_records_cannot_influence_live_learning():
    assert "USER_CONFIRMED_RECONSTRUCTION_NOT_HISTORICAL_EXACT" not in lessons._ALLOWED_STATUSES


def test_constitutional_reasoning_exact_gold_star_is_loaded():
    result = lessons.select_lesson("What is constitutional reasoning in the Archive's sense?")
    assert result
    assert result["exact"] is True
    assert result["benchmark_id"] == "gs-2026-11-15-constitutional-reasoning-archives-sense"
