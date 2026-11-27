import main


def test_humility_and_spiritual_maturity_relationship_selects_verified_archive_doorway():
    question = "What is the relationship between humility and spiritual maturity?"
    family = main._select_verified_doorway_conceptual_family(question)
    assert family == "humility_spiritual_maturity"
    doorway = main._VERIFIED_CONCEPTUAL_FAMILY_DOORWAYS[family]
    assert doorway["title"] == "Spirituality Without Escapism: Staying Human During Awakening Narratives"
    assert doorway["url"] == (
        "https://geralddaquila.com/2026/11/10/"
        "spirituality-without-escapism-staying-human-during-awakening-narratives/"
    )
    assert "humility" in doorway["rationale"].lower()
    assert "lived conduct" in doorway["rationale"].lower()


def test_unrelated_humility_or_spirituality_questions_do_not_capture_the_doorway():
    assert main._select_verified_doorway_conceptual_family("What does humility mean?") is None
    assert main._select_verified_doorway_conceptual_family("What is spiritual maturity?") is None
