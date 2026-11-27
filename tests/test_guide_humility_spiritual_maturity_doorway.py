import main
import general_guide_composition as composition


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


def test_adjacent_psychological_integration_questions_do_not_capture_the_doorway():
    unrelated_questions = (
        "Why does psychological integration matter more than spiritual performance?",
        "How can I integrate difficult emotions without turning spirituality into performance?",
        "What is the relationship between humility and psychological integration?",
        "What is the relationship between spiritual maturity and psychological integration?",
    )
    for question in unrelated_questions:
        assert main._select_verified_doorway_conceptual_family(question) is None, question



def test_terminal_humility_family_doorway_overrides_generic_preselected_candidate(monkeypatch):
    question = "What is the relationship between humility and spiritual maturity?"
    monkeypatch.setattr(main, "_final_exact_gold_standard_authority", lambda _query: None)
    payload = {
        "recommendation": {
            "title": "Why Psychological Integration Matters More Than Spiritual Performance",
            "url": "https://geralddaquila.com/2026/06/05/why-psychological-integration-matters-more-than-spiritual-performance/",
            "rationale": "A broadly related earlier selection.",
        },
        "canonical_doorway": {
            "title": "Why Psychological Integration Matters More Than Spiritual Performance",
            "url": "https://geralddaquila.com/2026/06/05/why-psychological-integration-matters-more-than-spiritual-performance/",
            "rationale": "A broadly related earlier selection.",
        },
        "doorway_selection_status": "VERIFIED_RELEVANT_DESTINATION",
        "doorway_selection_evaluated": True,
        "doorway_selection_source": "final_authoritative_recommendation_contract",
    }

    result = main._guide_restore_verified_doorway(payload, question)
    expected = main._VERIFIED_CONCEPTUAL_FAMILY_DOORWAYS["humility_spiritual_maturity"]

    assert result["recommendation"]["title"] == expected["title"]
    assert result["recommendation"]["url"] == expected["url"]
    assert result["canonical_doorway"] == result["recommendation"]
    assert result["doorway_selection_source"] == "reviewed_humility_spiritual_maturity_family"

def test_relational_answer_contract_distinguishes_humility_from_self_erasure():
    question = "What is the relationship between humility and spiritual maturity?"
    prompt = composition._build_general_guide_system_message(question)
    for required in (
        "HUMILITY AND SPIRITUAL MATURITY",
        "learning",
        "honest self-appraisal",
        "self-erasure",
        "diminished self-worth",
        "appropriate boundaries",
        "lived conduct",
    ):
        assert required in prompt


def test_relational_humility_contract_does_not_capture_adjacent_questions():
    unrelated_questions = (
        "What does humility mean?",
        "What is spiritual maturity?",
        "Why does psychological integration matter more than spiritual performance?",
        "How does humility relate to psychological integration?",
    )
    for question in unrelated_questions:
        prompt = composition._build_general_guide_system_message(question)
        assert "HUMILITY AND SPIRITUAL MATURITY" not in prompt, question
