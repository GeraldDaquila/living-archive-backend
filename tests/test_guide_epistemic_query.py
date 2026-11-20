from guide_epistemic_query import build_epistemic_retrieval_plan


def test_four_axis_epistemic_question_builds_relational_retrieval_plan():
    query = "What counts as evidence, interpretation, hypothesis, and normative judgment?"
    plan = build_epistemic_retrieval_plan(query)
    assert plan is not None
    assert plan["axes"] == [
        "evidence", "interpretation", "hypothesis", "normative_judgment"
    ]
    assert plan["axis_count"] == 4
    assert "provenance" in plan["retrieval_query"]
    assert "what ought to be" in plan["retrieval_query"]
    assert plan["original_query_preserved"] is True
    assert plan["doorway_authority"] == "unchanged_existing_canonical_gates"


def test_three_axis_synonyms_are_recognized():
    plan = build_epistemic_retrieval_plan(
        "How do facts, inferences, and testable explanations differ?"
    )
    assert plan is not None
    assert plan["axes"] == ["evidence", "interpretation", "hypothesis"]


def test_two_axis_question_does_not_overexpand():
    assert build_epistemic_retrieval_plan(
        "What is the difference between evidence and interpretation?"
    ) is None


def test_flat_list_without_relational_question_does_not_overexpand():
    assert build_epistemic_retrieval_plan(
        "Evidence, interpretation, hypothesis, and normative judgment"
    ) is None


def test_unrelated_question_does_not_trigger_epistemic_plan():
    assert build_epistemic_retrieval_plan(
        "How can a community improve coordination?"
    ) is None
