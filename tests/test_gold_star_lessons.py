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



def test_unnumbered_approved_gold_stars_remain_loadable_and_selectable():
    import json
    from pathlib import Path

    registry_path = Path(lessons.__file__).resolve().parent / "docs" / "qa" / "gold_standard_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    unnumbered = next(
        record for record in registry["records"]
        if record.get("status") == "USER_APPROVED_GOLD_STANDARD"
        and record.get("gold_star_number") is None
        and record.get("runtime_transfer") is True
    )
    assert unnumbered["benchmark_id"] in {item["id"] for item in lessons._LESSONS}
    selected = lessons.select_lesson(unnumbered["query"])
    assert selected and selected["exact"] is True
    assert selected["benchmark_id"] == unnumbered["benchmark_id"]


def test_numbering_corruption_does_not_disable_adaptive_learning(tmp_path, monkeypatch):
    import json
    from pathlib import Path
    import pytest

    registry_path = Path(lessons.__file__).resolve().parent / "docs" / "qa" / "gold_standard_registry.json"
    review_path = Path(lessons.__file__).resolve().parent / "docs" / "qa" / "gold_star_qualitative_transfer_review.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    review = json.loads(review_path.read_text(encoding="utf-8"))
    damaged = next(
        record for record in registry["records"]
        if record.get("status") == "USER_APPROVED_GOLD_STANDARD"
        and isinstance(record.get("gold_star_number"), int)
    )
    damaged["gold_star_number"] = "SERIAL-METADATA-CORRUPTED"
    damaged["numbering_status"] = "ASSIGNED"
    bad_registry_path = tmp_path / "gold_standard_registry.json"
    review_copy_path = tmp_path / "gold_star_qualitative_transfer_review.json"
    bad_registry_path.write_text(json.dumps(registry), encoding="utf-8")
    review_copy_path.write_text(json.dumps(review), encoding="utf-8")
    monkeypatch.setattr(lessons, "_REGISTRY_PATH", bad_registry_path)
    monkeypatch.setattr(lessons, "_TRANSFER_REVIEW_PATH", review_copy_path)

    loaded = lessons._load_lessons()
    assert len(loaded) == sum(
        record.get("status") == "USER_APPROVED_GOLD_STANDARD"
        for record in registry["records"]
    )
    assert any(item["id"] == damaged["benchmark_id"] for item in loaded)
    with pytest.raises(lessons.GoldStarRegistryIntegrityError):
        lessons.validate_numbering_integrity(
            registry["records"],
            registry.get("numbering_gap_register"),
            registry.get("numbering_policy"),
        )


def test_combined_registry_integrity_still_enforces_numbering():
    import json
    from pathlib import Path
    import pytest

    registry_path = Path(lessons.__file__).resolve().parent / "docs" / "qa" / "gold_standard_registry.json"
    review_path = Path(lessons.__file__).resolve().parent / "docs" / "qa" / "gold_star_qualitative_transfer_review.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    review = json.loads(review_path.read_text(encoding="utf-8"))
    damaged = next(
        record for record in registry["records"]
        if record.get("status") == "USER_APPROVED_GOLD_STANDARD"
        and isinstance(record.get("gold_star_number"), int)
    )
    damaged["gold_star_number"] = "SERIAL-METADATA-CORRUPTED"
    with pytest.raises(lessons.GoldStarRegistryIntegrityError):
        lessons.validate_registry_integrity(
            registry["records"],
            review["entries"],
            registry.get("numbering_gap_register"),
            registry.get("numbering_policy"),
        )


def test_active_quality_contribution_exposes_only_bounded_structural_guidance():
    result = lessons.active_quality_contribution(
        "What is spiritual bypassing, and why does it matter?"
    )
    assert result
    assert result["authority_mode"] == "structural_guidance_only"
    assert result["discipline"]
    assert result["abstention_boundary"]
    assert "expected_response" not in result
    assert "doorway" not in result



def test_deterministic_fallback_eligibility_is_explicit_not_inferred_from_adaptive_activation(tmp_path, monkeypatch):
    import json
    from pathlib import Path

    registry_path = Path(lessons.__file__).resolve().parent / "docs" / "qa" / "gold_standard_registry.json"
    review_path = Path(lessons.__file__).resolve().parent / "docs" / "qa" / "gold_star_qualitative_transfer_review.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    review = json.loads(review_path.read_text(encoding="utf-8"))
    target = next(
        record for record in registry["records"]
        if record.get("status") == "USER_APPROVED_GOLD_STANDARD"
        and record.get("runtime_transfer") is True
    )
    target.setdefault("gold_star_capabilities", {})["active_quality_contributor"] = True
    target["gold_star_capabilities"]["deterministic_fallback_eligible"] = False
    target_id = target["benchmark_id"]
    bad_registry_path = tmp_path / "gold_standard_registry.json"
    review_copy_path = tmp_path / "gold_star_qualitative_transfer_review.json"
    bad_registry_path.write_text(json.dumps(registry), encoding="utf-8")
    review_copy_path.write_text(json.dumps(review), encoding="utf-8")
    monkeypatch.setattr(lessons, "_REGISTRY_PATH", bad_registry_path)
    monkeypatch.setattr(lessons, "_TRANSFER_REVIEW_PATH", review_copy_path)

    loaded = lessons._load_lessons()
    item = next(record for record in loaded if record["id"] == target_id)
    assert item["runtime_transfer"] is True
    assert item["deterministic_fallback_eligible"] is False


def test_cross_question_gold_star_contribution_cannot_claim_deterministic_answer_authority():
    result = lessons.active_quality_contribution(
        "How do local choices relate to wider institutional and social circumstances?"
    )
    assert result
    assert result["exact"] is False
    assert result["authority_mode"] == "structural_guidance_only"
    assert "expected_response" not in result
    assert "deterministic_fallback_eligible" not in result


def test_deterministic_fallback_contribution_requires_explicit_capability():
    import copy
    target = next(
        item for item in lessons._LESSONS
        if item["runtime_transfer"] and item.get("deterministic_fallback_eligible")
    )
    eligible = copy.deepcopy(target)
    ineligible = copy.deepcopy(target)
    ineligible["deterministic_fallback_eligible"] = False
    original = lessons._LESSONS
    try:
        lessons._LESSONS = [ineligible]
        assert lessons.deterministic_fallback_contribution(target["query"]) is None
        lessons._LESSONS = [eligible]
        contribution = lessons.deterministic_fallback_contribution(target["query"])
        assert contribution
        assert contribution["authority_mode"] == "deterministic_structural_guidance_only"
        assert contribution["discipline"] and contribution["abstention_boundary"]
        assert "expected_response" not in contribution and "doorway" not in contribution
    finally:
        lessons._LESSONS = original


def test_deterministic_fallback_guidance_is_applied_without_changing_paragraph_count():
    target = next(
        item for item in lessons._LESSONS
        if item["runtime_transfer"] and item.get("deterministic_fallback_eligible")
    )
    response = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    guided = lessons.apply_deterministic_fallback_guidance(target["query"], response)
    assert "A useful way to examine this is:" in guided
    assert target["transferable_discipline"] in guided
    assert target["abstention_boundary"] in guided
    assert len([p for p in guided.split("\n\n") if p.strip()]) == 3
    assert lessons.apply_deterministic_fallback_guidance(target["query"], guided) == guided


def test_deterministic_fallback_guidance_ignores_unflagged_analogues():
    import copy
    target = next(
        item for item in lessons._LESSONS
        if item["runtime_transfer"] and item.get("deterministic_fallback_eligible")
    )
    unflagged = copy.deepcopy(target)
    unflagged["deterministic_fallback_eligible"] = False
    original = lessons._LESSONS
    try:
        lessons._LESSONS = [unflagged]
        response = "A bounded deterministic answer."
        assert lessons.apply_deterministic_fallback_guidance(target["query"], response) == response
    finally:
        lessons._LESSONS = original


def test_sacred_language_power_gold_star_is_loaded_as_approved_structural_learning():
    result = lessons.select_lesson(
        "How can sacred language clarify experience, and how can it obscure power relations?"
    )
    assert result and result["exact"] is True
    assert result["benchmark_id"] == "gs-2026-11-14-sacred-language-clarity-power-live-candidate"
    contribution = lessons.active_quality_contribution(
        "How can sacred language clarify experience, and how can it obscure power relations?"
    )
    assert contribution
    assert contribution["reasoning_family"] == "sacred_language_and_power"
    assert contribution["authority_mode"] == "structural_guidance_only"
    assert "expected_response" not in contribution and "doorway" not in contribution


def test_sacred_language_gold_star_preserves_existing_explicit_deterministic_capability():
    selected = lessons.select_lesson(
        "How can sacred language clarify experience, and how can it obscure power relations?"
    )
    assert selected and selected["exact"] is True
    assert selected["deterministic_fallback_eligible"] is True



def test_community_wisdom_gold_star_is_active_structural_learning_not_deterministic_fallback():
    query = "How can communities preserve wisdom without treating tradition as infallible?"
    result = lessons.select_lesson(query)
    assert result and result["exact"] is True
    assert result["benchmark_id"] == "gs-2026-11-16-community-wisdom-tradition-epistemic-stewardship"
    assert result["runtime_transfer"] is True
    assert result["deterministic_fallback_eligible"] is False
    contribution = lessons.active_quality_contribution(query)
    assert contribution
    assert contribution["authority_mode"] == "structural_guidance_only"
    assert contribution["reasoning_family"] == "integrative_stewardship_epistemic_humility_human_accountability"
    assert "expected_response" not in contribution and "doorway" not in contribution
    assert lessons.deterministic_fallback_contribution(query) is None
