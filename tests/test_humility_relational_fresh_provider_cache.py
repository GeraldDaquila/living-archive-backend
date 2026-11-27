"""Fresh provider execution is required for the reviewed humility/maturity relation probe."""

from general_guide_composition import _requires_fresh_provider_composition


def test_humility_spiritual_maturity_relational_questions_bypass_composition_cache():
    for query in (
        "What is the relationship between humility and spiritual maturity?",
        "How do humility and spiritual maturity relate to one another?",
        "Explain the connection between spiritual maturity and humility.",
    ):
        assert _requires_fresh_provider_composition(query), query


def test_adjacent_humility_or_spirituality_questions_keep_normal_cache_policy():
    for query in (
        "What does humility mean?",
        "What is spiritual maturity?",
        "What is the relationship between humility and psychological integration?",
        "What is the relationship between transparency and trust?",
    ):
        assert not _requires_fresh_provider_composition(query), query
