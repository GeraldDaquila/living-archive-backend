import general_guide_composition as composition


QUESTION = "Why can growth become destructive when detached from ecological and social limits?"


def test_growth_within_living_limits_contract_recovers_off_task_template():
    off_task = (
        "The most useful explanation begins by distinguishing the immediate event from the conditions that made it more likely. "
        "A visible incident may be the trigger without being the whole cause.\n\n"
        "Look at the evidence, incentives, constraints, relationships, and decisions involved, and compare more than one plausible explanation.\n\n"
        "These are possibilities to test, not conclusions about a specific case."
    )
    repaired = composition.enforce_response_contracts(QUESTION, off_task)
    assert composition._has_growth_within_living_limits_explanation(repaired)
    assert "immediate event" not in repaired.casefold()
    assert "ecological" in repaired.casefold()
    assert "social" in repaired.casefold()


def test_growth_contract_does_not_capture_unrelated_growth_question():
    assert not composition._requires_growth_within_living_limits(
        "Why do companies sometimes pursue growth?"
    )
