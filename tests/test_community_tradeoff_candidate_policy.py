import gold_star_lessons as lessons


def _selected(query):
    return lessons.select_lesson_candidates(query, limit=4)


def test_community_freedom_responsibility_tradeoff_selects_governed_guidance():
    query = (
        "When a community faces a difficult trade-off between individual freedom "
        "and shared responsibility, how should it make a decision that is both fair and workable?"
    )
    selected = _selected(query)
    ids = [item["benchmark_id"] for item in selected]
    # The exact, user-approved production exemplar takes precedence for this
    # exact question. The broader governed trade-off policy remains covered by
    # the paraphrase and required-core tests below.
    assert ids == [
        "gs-2026-11-22-community-freedom-shared-responsibility-decision",
    ]
    assert selected[0]["exact"] is True


def test_stakeholder_obligations_are_added_only_when_explicit():
    query = (
        "A community must choose between competing obligations to several stakeholders; "
        "how can it make a fair decision while respecting freedom and responsibility?"
    )
    selected = _selected(query)
    assert "general-guide-competing-stakeholder-obligations-gold-standard-2026-10-26" in {
        item["benchmark_id"] for item in selected
    }


def test_ordinary_household_or_chores_questions_do_not_activate_policy():
    for query in (
        "How should roommates divide household chores fairly?",
        "How should a community organize a shared garden?",
        "Who is responsible for this?",
        "What is individual freedom?",
    ):
        assert _selected(query) == [] or all(
            item.get("match_basis") != "governed_community_tradeoff_policy"
            for item in _selected(query)
        )


def test_missing_required_core_candidates_fail_closed(monkeypatch):
    import community_tradeoff_candidate_policy as policy

    required_core_ids = {
        "general-guide-ethical-tradeoff-2026-10",
        "gs-2026-11-22-community-freedom-shared-responsibility-decision",
    }
    lessons_without_core = [
        item for item in lessons._LESSONS if item["id"] not in required_core_ids
    ]
    assert policy.select_community_tradeoff_candidates(
        "When a community faces a difficult trade-off between individual freedom "
        "and shared responsibility, how should it make a decision that is both fair and workable?",
        lessons_without_core,
    ) == []



def test_active_contribution_carries_selected_disciplines_and_boundaries():
    query = (
        "When a community faces a difficult trade-off between individual freedom "
        "and shared responsibility, how should it make a decision that is both fair and workable?"
    )
    contribution = lessons.active_quality_contribution(query)
    assert contribution is not None
    assert contribution["authority_mode"] == "structural_guidance_only"
    assert contribution["benchmark_id"] == "gs-2026-11-22-community-freedom-shared-responsibility-decision"
    candidates = contribution["candidates"]
    assert [item["benchmark_id"] for item in candidates] == [
        "gs-2026-11-22-community-freedom-shared-responsibility-decision",
    ]
    assert all(item["discipline"].strip() for item in candidates)
    assert all(item["abstention_boundary"].strip() for item in candidates)


def test_new_community_freedom_gold_star_transfers_to_a_close_paraphrase():
    query = (
        "How should a community balance personal liberty with collective obligations "
        "when setting a fair rule?"
    )
    selected = _selected(query)
    ids = [item["benchmark_id"] for item in selected]
    target = "gs-2026-11-23-community-rule-design-liberty-shared-obligations"
    assert target in ids
    candidate = next(item for item in selected if item["benchmark_id"] == target)
    assert candidate["exact"] is False
    assert candidate["match_basis"] == "governed_community_tradeoff_policy"
    assert candidate["transferable_discipline"]
    assert candidate["abstention_boundary"]


def test_paraphrase_contribution_includes_new_gold_star_as_structural_guidance_only():
    query = (
        "How should a community balance personal liberty with collective obligations "
        "when setting a fair rule?"
    )
    contribution = lessons.active_quality_contribution(query)
    assert contribution is not None
    assert contribution["authority_mode"] == "structural_guidance_only"
    assert contribution["benchmark_id"] == "gs-2026-11-23-community-rule-design-liberty-shared-obligations"
    assert contribution["exact"] is False
    assert contribution["abstention_boundary"]
