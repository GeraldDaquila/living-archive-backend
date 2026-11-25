"""Regression tests for discriminative Gold Star subject matching."""

import gold_star_lessons


def test_generic_quantifier_does_not_establish_subject_identity():
    assert not ({"one", "rather", "than"} & gold_star_lessons._concept_terms("one master cause rather than one cause"))


def test_heldout_multicausal_query_prefers_societal_breakdown_gold_star():
    query = (
        "How can we explain societal breakdown through interacting causes "
        "rather than one master cause?"
    )
    selected = gold_star_lessons.select_lesson(query)
    assert selected is not None
    assert selected["benchmark_id"] == (
        "general-guide-systems-intelligibility-without-monocausal-reduction-gold-star-2026-11-13"
    )
    assert selected["exact"] is False
