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


def test_community_rule_design_gold_star_transfers_conditionally_to_rule_policy_paraphrase():
    query = (
        "How should a community decide whether limits on personal liberty are justified "
        "by shared obligations and risks?"
    )
    selected = _selected(query)
    ids = [item["benchmark_id"] for item in selected]
    target = "gs-2026-11-23-community-rule-design-liberty-shared-obligations"
    assert target in ids
    candidate = next(item for item in selected if item["benchmark_id"] == target)
    assert candidate["exact"] is False
    assert candidate["match_basis"] == "governed_community_tradeoff_policy"
    assert candidate["role"] == "conditional"
    assert candidate["activation_condition"]
    assert candidate["transferable_discipline"]
    assert candidate["abstention_boundary"]


def test_rule_design_paraphrase_contribution_includes_new_gold_star_as_conditional_structural_guidance():
    query = (
        "How should a community decide whether limits on personal liberty are justified "
        "by shared obligations and risks?"
    )
    contribution = lessons.active_quality_contribution(query)
    assert contribution is not None
    assert contribution["authority_mode"] == "structural_guidance_only"
    assert contribution["benchmark_id"] == "gs-2026-11-22-community-freedom-shared-responsibility-decision"
    candidate = next(item for item in contribution["candidates"] if item["benchmark_id"] == "gs-2026-11-23-community-rule-design-liberty-shared-obligations")
    assert candidate["exact"] is False
    assert candidate["role"] == "conditional"
    assert candidate["discipline"]
    assert candidate["abstention_boundary"]

def test_new_rule_design_gold_star_exact_match_does_not_grant_exact_answer_authority():
    query = (
        "How should a community balance personal liberty with collective obligations "
        "when setting a fair rule?"
    )
    selected = _selected(query)
    assert len(selected) == 1
    assert selected[0]["benchmark_id"] == "gs-2026-11-23-community-rule-design-liberty-shared-obligations"
    assert selected[0]["exact"] is True
    contribution = lessons.active_quality_contribution(query)
    assert contribution is not None
    assert contribution["authority_mode"] == "structural_guidance_only"
    assert contribution["exact"] is True
    import json
    from pathlib import Path
    registry = json.loads((Path(__file__).resolve().parents[1] / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    record = next(item for item in registry["records"] if item["benchmark_id"] == selected[0]["benchmark_id"])
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False

