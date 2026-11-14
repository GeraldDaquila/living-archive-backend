from general_guide_composition import _conceptual_relationship_recovery


def test_meaning_making_and_factual_explanation_receive_direct_orientation():
    response = _conceptual_relationship_recovery(
        "What is the difference between meaning-making and factual explanation?"
    )

    assert response
    lowered = response.casefold()
    assert "factual explanation" in lowered
    assert "meaning-making" in lowered
    assert "different questions" in lowered
    assert "evidence alone does not settle every question of significance" in lowered
    assert "i do not have enough grounded material" not in lowered


def test_meaning_making_orientation_preserves_the_evidence_interpretation_boundary():
    response = _conceptual_relationship_recovery(
        "How do meaning-making and factual explanation differ?"
    )

    assert response
    lowered = response.casefold()
    assert "interpretation from being mistaken for evidence" in lowered
    assert "facts can constrain meaning-making" in lowered
