import gold_star_lessons as lessons


def test_only_explicitly_approved_records_are_loaded():
    assert lessons._LESSONS
    assert lessons._ALLOWED_STATUSES == frozenset({"USER_APPROVED_GOLD_STANDARD"})


def test_exact_question_preserves_its_canonical_runtime_transfer_setting():
    result = lessons.select_lesson("What is institutional memory, and why does it matter?")
    assert result and result["exact"] is True
    assert result["runtime_transfer"] is True


def test_explicit_transfer_matches_active_structure_agency_lesson():
    result = lessons.select_lesson(
        "How do local choices relate to wider institutional and social circumstances?"
    )
    assert result
    assert result["benchmark_id"] == "general-guide-cross-scale-orientation-refined-gold-standard-2026-11-15"
    assert result["exact"] is False


def test_active_approved_gold_star_is_loaded_for_runtime_transfer():
    matching = [
        record for record in lessons._LESSONS
        if record["id"] == "general-guide-cross-scale-orientation-refined-gold-standard-2026-11-15"
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



def test_numbered_spiritual_bypassing_gold_star_remains_adaptive_learning_eligible():
    import json
    from pathlib import Path
    registry_path = Path(lessons.__file__).resolve().parent / "docs" / "qa" / "gold_standard_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    record = next(
        r for r in registry["records"]
        if r["benchmark_id"] == "gs-2026-11-14-bounded-conceptual-orientation-spiritual-bypassing"
    )
    assert record["numbering_status"] == "ASSIGNED"
    assert record["gold_star_number"] == 91
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    selected = lessons.select_lesson("What is spiritual bypassing, and why does it matter?")
    assert selected and selected["exact"] is True
    assert selected["benchmark_id"] == record["benchmark_id"]
