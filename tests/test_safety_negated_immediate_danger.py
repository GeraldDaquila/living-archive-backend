"""Negated generic danger language must not become an acute crisis interruption."""

from safety_intelligence import (
    SAFETY_INTELLIGENCE_CONTRACT_VERSION,
    classify_safety,
    normalize_safety_state,
)


NON_ACUTE_THIRD_PERSON = (
    "A person in the Philippines feels overwhelmed and is not in immediate danger, "
    "but wants someone to talk to. What support resources are available?"
)


def test_explicit_non_acute_third_person_support_does_not_trigger_crisis_boundary():
    assert normalize_safety_state(NON_ACUTE_THIRD_PERSON) is None
    assert classify_safety(NON_ACUTE_THIRD_PERSON) is None


def test_direct_first_person_self_harm_disclosure_still_overrides_negation():
    assert normalize_safety_state("I am not in immediate danger, but I want to die.") == "acute"
    assert classify_safety("I am not in immediate danger, but I want to die.") == "acute"


def test_support_for_someone_at_risk_remains_in_the_support_lane():
    query = "Someone I know is thinking about suicide and I want to help them."
    assert normalize_safety_state(query) == "support"
    assert classify_safety(query) == "support"


def test_safety_contract_version_advances():
    assert SAFETY_INTELLIGENCE_CONTRACT_VERSION == "v2.8"
