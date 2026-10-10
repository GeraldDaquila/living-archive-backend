"""Regression tests for lived relational projection routing in The Guide."""

import main


def test_projection_uncertainty_opens_hrn_boundary():
    query = "I can't tell whether what I'm sensing in a relationship is real or something I'm projecting."
    decision = main._relational_boundary_decision(query)

    assert decision["open"] is True
    assert decision["reason"] == "lived_relational_structure"
    assert decision["signals"]["first_person"] is True
    assert decision["signals"]["relational_term"] is True
    assert decision["signals"]["dynamic"] is True
    assert decision["signals"]["inquiry"] is True


def test_explicit_archive_resource_search_stays_outside_hrn_boundary():
    query = "Can you find an article in the Living Archive about projection in relationships?"
    decision = main._relational_boundary_decision(query)

    assert decision["open"] is False
    assert decision["reason"] == "bounded_archive_or_definition_request"
