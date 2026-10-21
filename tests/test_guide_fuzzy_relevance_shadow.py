"""Tests for explainable fuzzy relevance shadow scoring."""

from guide_fuzzy_relevance import score_resource_fit

QUERY = ("What if repairing the harm to one group would create a different harm for another group? "
         "How should the decision-makers work through that conflict?")

def test_direct_ethical_tradeoff_resource_scores_higher_than_adjacent_belonging_article():
    direct = {
        "title": "Ethical Trade-offs When Repairing Harm",
        "text": ("When repairing harm creates competing harms, decision-makers should consider who bears the burden, "
                 "protect rights, compare alternatives, and listen to affected people in a fair process. Review consequences.")
    }
    adjacent = {
        "title": "The Tightrope of Belonging: Group Affiliation and Authenticity",
        "text": "This essay explores belonging, group affiliation, authenticity, and identity in a community."
    }
    direct_score = score_resource_fit(QUERY, direct)
    adjacent_score = score_resource_fit(QUERY, adjacent)
    assert direct_score["ethical_tradeoff"] > adjacent_score["ethical_tradeoff"]
    assert direct_score["overall_shadow_score"] > adjacent_score["overall_shadow_score"]

def test_scores_are_bounded_and_explainable():
    score = score_resource_fit(QUERY, {"title": "Ethical Trade-offs", "text": "Competing harms require a fair process."})
    assert all(0.0 <= value <= 1.0 for value in score.values())
    assert "ethical_tradeoff" in score
    assert "harm_repair" in score
    assert "power_fairness" in score
    assert "query_title_overlap" in score
    assert "query_body_overlap" in score

def test_empty_resource_is_safe_and_scores_zero():
    score = score_resource_fit(QUERY, {})
    assert all(value == 0.0 for value in score.values())

def test_scoring_does_not_modify_candidate():
    candidate = {"title": "Ethical Trade-offs", "text": "Competing harms require a fair process."}
    before = dict(candidate)
    score_resource_fit(QUERY, candidate)
    assert candidate == before
