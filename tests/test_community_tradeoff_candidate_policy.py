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


def test_missing_required_core_candidate_fails_closed(monkeypatch):
    import community_tradeoff_candidate_policy as policy

    lessons_without_core = [
        item for item in lessons._LESSONS
        if item["id"] != "general-guide-ethical-tradeoff-2026-10"
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
