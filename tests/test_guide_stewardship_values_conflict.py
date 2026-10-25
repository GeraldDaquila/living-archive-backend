from general_guide_composition import (
    _faithful_stewardship_values_conflict_recovery,
    _has_faithful_stewardship_values_conflict,
    _requires_faithful_stewardship_values_conflict,
    enforce_response_contracts,
)

QUESTION = "What does faithful stewardship require when values conflict?"


def test_recognizes_values_conflict_inquiry_but_not_simple_glossary_lookup():
    assert _requires_faithful_stewardship_values_conflict(QUESTION)
    assert not _requires_faithful_stewardship_values_conflict("What does stewardship mean?")
    assert not _requires_faithful_stewardship_values_conflict("What are the values of the Living Archive?")


def test_generic_response_is_replaced_by_substantive_three_paragraph_answer():
    generic = (
        "A practical way to approach faithful stewardship when values conflict is to define "
        "the outcome you want, identify the main constraint, and choose one step small enough "
        "to test. Before acting, consider who else is affected and what could go wrong. "
        "Check the result against the original goal and adjust rather than assuming the first "
        "attempt must be final."
    )
    answer = enforce_response_contracts(QUESTION, generic)
    assert answer != generic
    assert _has_faithful_stewardship_values_conflict(answer)
    assert len([p for p in answer.split("\\n\\n") if p.strip()]) == 3
    for phrase in ("what is actually in tension", "who is affected", "accountable to those affected"):
        assert phrase in answer.casefold()


def test_recovery_answer_passes_contract_and_contains_conflict_standards():
    answer = _faithful_stewardship_values_conflict_recovery()
    assert _has_faithful_stewardship_values_conflict(answer)
    assert len([p for p in answer.split("\\n\\n") if p.strip()]) == 3


def test_generic_action_planning_fails_substantive_contract():
    assert not _has_faithful_stewardship_values_conflict(
        "Define the outcome you want and choose one step small enough to test."
    )
