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
    assert ids == [
        "general-guide-ethical-tradeoff-2026-10",
        "gs-2026-11-20-power-responsibility-proportional-accountability",
        "gs-2026-11-20-stewardship-consent-relational-legitimacy",
    ]
    assert [item["role"] for item in selected] == ["core", "conditional", "conditional"]
    assert all(item["match_basis"] == "governed_community_tradeoff_policy" for item in selected)
    assert all(item["score"] is None for item in selected)


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
