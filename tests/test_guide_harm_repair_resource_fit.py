"""Regression tests for resource relevance on harm-repair adequacy questions."""

import main


QUERY = (
    "What should the group do if the people who suffered the harm say that its "
    "proposed repair does not address what they actually lost?"
)


def _doc(title, text):
    return {"title": title, "text": text}


def test_personal_growth_article_is_rejected_for_harm_repair_question():
    decoy = _doc(
        "When You Outgrow the Person You Once Had to Be",
        (
            "An essay about personal growth, identity, changing relationships, "
            "and becoming a different version of yourself."
        ),
    )
    assert not main._harm_repair_candidate_has_direct_fit(QUERY, decoy)


def test_restorative_justice_resource_with_direct_repair_evidence_is_accepted():
    relevant = _doc(
        "Restorative Justice and Repairing Harm",
        (
            "Restorative justice brings people affected by harm into a process "
            "that listens to their needs and considers what was lost. Repair may "
            "include restitution, acknowledging harm, making amends, and giving "
            "affected people a meaningful voice in deciding what repair requires."
        ),
    )
    assert main._harm_repair_candidate_has_direct_fit(QUERY, relevant)


def test_generic_governance_title_alone_is_not_enough():
    weak = _doc(
        "Regenerative Governance Principles",
        (
            "This resource discusses leadership, shared purpose, long-term "
            "institutional health, and collaborative decision-making."
        ),
    )
    assert not main._harm_repair_candidate_has_direct_fit(QUERY, weak)


def test_harm_repair_gate_does_not_overconstrain_unrelated_questions():
    unrelated_query = "What should the group do if members disagree about the schedule?"
    generic_resource = _doc(
        "When You Outgrow the Person You Once Had to Be",
        "An essay about personal growth and changing relationships.",
    )
    assert main._harm_repair_candidate_has_direct_fit(unrelated_query, generic_resource)
