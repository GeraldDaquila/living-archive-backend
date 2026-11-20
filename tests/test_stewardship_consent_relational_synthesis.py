"""Regression tests for relational synthesis of stewardship and consent."""

import general_guide_composition as composition


QUERY = "What is the relationship between stewardship and consent?"


def test_stewardship_consent_query_activates_relational_synthesis():
    assert composition._requires_discernment_synthesis(QUERY)
    assert composition._requires_stewardship_consent_relationship(QUERY)


def test_plain_stewardship_definition_does_not_activate_consent_contract():
    assert not composition._requires_stewardship_consent_relationship(
        "What is stewardship?"
    )


def test_complete_stewardship_consent_synthesis_passes():
    answer = (
        "Stewardship creates a responsibility to care for what is entrusted to you, "
        "while consent establishes whether and within what limits other people may "
        "be involved. Being entrusted with responsibility does not automatically "
        "grant authority to decide for affected people. Consent protects their "
        "agency, including their ability to refuse or renegotiate participation."
    )
    assert composition._has_stewardship_consent_relationship(answer)


def test_generic_stewardship_explanation_fails_relationship_contract():
    answer = (
        "Stewardship means taking care of something entrusted to you. "
        "It matters because ordinary choices accumulate and responsible care "
        "helps preserve trust and usefulness."
    )
    assert not composition._has_stewardship_consent_relationship(answer)


def test_consent_must_not_be_reduced_to_consultation():
    answer = (
        "Stewardship creates responsibility, but it does not automatically confer "
        "authority. Consent is not merely consultation; it protects the agency "
        "and right of affected people to refuse."
    )
    assert composition._has_stewardship_consent_relationship(answer)
