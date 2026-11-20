from guide_incomplete_knowledge import build_incomplete_knowledge_plan


def test_incomplete_knowledge_stewardship_question_gets_full_contract():
    query = "How should a steward act amid incomplete knowledge?"
    plan = build_incomplete_knowledge_plan(query)
    assert plan is not None
    assert plan["task_class"] == "stewardship_under_incomplete_knowledge"
    assert set(plan["required_dimensions"]) == {
        "known_inferred_assumed_unknown",
        "confidence_and_missing_perspectives",
        "stakes_urgency_authority_and_reversibility",
        "proportionate_action_and_safeguards",
        "feedback_review_and_revision_conditions",
        "human_accountability_and_ai_boundary",
    }
    architectural = plan["architectural_contract"].casefold()
    for phrase in (
        "directly known", "inferred", "assumed", "unknown",
        "reversibility", "affected people's situated knowledge",
        "least harmful protective action", "reviewed",
        "continuation, adaptation, reversal, or stopping",
        "ai and other tools", "accountability",
    ):
        assert phrase in architectural
    query_contract = plan["composition_instruction"].casefold()
    for phrase in (
        "answer how to act", "what can safely be done now",
        "deferred, or escalated", "observable signals",
        "conditions for changing or stopping course",
        "retain any independently verified",
    ):
        assert phrase in query_contract


def test_stewardship_uncertainty_contract_handles_natural_variants():
    variants = [
        "How can stewardship proceed when the facts are uncertain?",
        "What should a custodian do when key information is unknown?",
        "How should a steward decide with limited information?",
    ]
    for query in variants:
        assert build_incomplete_knowledge_plan(query) is not None


def test_unrelated_uncertainty_or_stewardship_questions_do_not_trigger():
    variants = [
        "What is uncertainty in science?",
        "What does stewardship mean?",
        "How should a project manager act amid incomplete knowledge?",
        "",
    ]
    for query in variants:
        assert build_incomplete_knowledge_plan(query) is None


def test_contract_is_scoped_to_shared_composition_and_query_instruction():
    from pathlib import Path
    source = Path("general_guide_composition.py").read_text(encoding="utf-8")
    assert "from guide_incomplete_knowledge import build_incomplete_knowledge_plan" in source
    assert "build_incomplete_knowledge_plan(question)" in source
    assert "+ incomplete_knowledge_instruction" in source
    assert 'incomplete_knowledge_plan["architectural_contract"]' in source
