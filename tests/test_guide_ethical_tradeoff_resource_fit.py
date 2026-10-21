"""Regression tests for direct resource fit on conflicting-harm questions."""

import main

QUERY = ("What if repairing the harm to one group would create a different harm for another group? "
         "How should the decision-makers work through that conflict?")

def _doc(title, text):
    return {"title": title, "text": text}

def test_group_belonging_article_is_rejected_when_only_adjacent():
    doc = _doc("The Tightrope of Belonging: Navigating Group Affiliation",
               "This essay explores belonging, group affiliation, and authenticity.")
    assert not main._ethical_tradeoff_candidate_has_direct_fit(QUERY, doc)

def test_direct_tradeoff_resource_is_accepted():
    doc = _doc("Ethical Trade-offs When Repairing Harm",
               "When repairing harm creates competing harms, decision-makers should consider who bears the burden, protect rights, compare alternatives, and listen to affected people in a fair process.")
    assert main._ethical_tradeoff_candidate_has_direct_fit(QUERY, doc)

def test_generic_governance_resource_is_rejected():
    doc = _doc("Regenerative Governance Principles",
               "This resource discusses shared leadership, collective purpose, and institutional health.")
    assert not main._ethical_tradeoff_candidate_has_direct_fit(QUERY, doc)

def test_unrelated_belonging_question_keeps_normal_resource_behavior():
    doc = _doc("The Tightrope of Belonging", "An essay exploring belonging and authenticity.")
    assert main._ethical_tradeoff_candidate_has_direct_fit("How can a group build belonging?", doc)
