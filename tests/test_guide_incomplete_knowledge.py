from guide_incomplete_knowledge import (
    build_incomplete_knowledge_plan,
    build_incomplete_knowledge_recovery,
    incomplete_knowledge_response_meets_contract,
)


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
        "directly known facts", "interpretations and inferences", "assumptions",
        "material unknowns", "reversibility", "situated knowledge",
        "least harmful protective action", "review point or trigger",
        "continuation, adaptation, reversal, or stopping",
        "ai and other tools", "accountability",
    ):
        assert phrase in architectural
    query_contract = plan["composition_instruction"].casefold()
    for phrase in (
        "give a practical method for acting under uncertainty", "what can safely be done now",
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
    assert 'parts.append(incomplete_knowledge_plan.get("architectural_contract", ""))' in source
    assert "_build_general_guide_system_message(" in source


def test_incomplete_knowledge_contract_requires_actionable_epistemic_and_correction_moves():
    plan = build_incomplete_knowledge_plan("How should a steward act amid incomplete knowledge?")
    architectural = plan["architectural_contract"].casefold()
    query = plan["composition_instruction"].casefold()
    for phrase in (
        "directly observed", "interpretations and inferences", "assumptions",
        "material unknowns", "situated knowledge", "confidence",
        "legitimate authority", "delay itself creates serious or imminent harm",
        "observable signals", "accountable for monitoring", "adaptation, reversal",
        "remain correctable",
    ):
        assert phrase in architectural
    for phrase in (
        "what is known and not known", "what the situation allows now",
        "how to act proportionately", "how to remain correctable",
        "what to monitor", "who is accountable", "waiting is unsafe",
        "do not merely say",
    ):
        assert phrase in query
    assert plan["version"] == "1.2"



def test_deterministic_recovery_covers_all_required_decision_moves():
    query = "How should a steward act amid incomplete knowledge?"
    recovery = build_incomplete_knowledge_recovery(query)
    assert recovery is not None
    assert recovery["task_class"] == "stewardship_under_incomplete_knowledge"
    assert recovery["version"] == "1.2"
    assert incomplete_knowledge_response_meets_contract(recovery["response"])


def test_generic_provider_exhaustion_answer_fails_the_contract():
    generic = (
        "Start by defining the outcome and responsibilities. Compare options, "
        "consider what each may damage, and remain accountable for what follows."
    )
    assert not incomplete_knowledge_response_meets_contract(generic)


def test_final_visitor_boundary_enforces_recovery_without_replacing_doorway_selection():
    from pathlib import Path
    source = Path("main.py").read_text(encoding="utf-8")
    finalizer = source.split("def _guide_finalize_visitor_payload(payload, query):", 1)[1]
    finalizer = finalizer.split("\ndef ", 1)[0]
    assert "build_incomplete_knowledge_plan(query)" in finalizer
    assert "incomplete_knowledge_response_meets_contract(current_response)" in finalizer
    assert "build_incomplete_knowledge_recovery(query)" in finalizer
    assert "_guide_reconcile_verified_doorway_recovery(safe)" in finalizer
    assert 'safe["processing"] = "final_visitor_boundary_stewardship_incomplete_knowledge_recovery"' in finalizer
