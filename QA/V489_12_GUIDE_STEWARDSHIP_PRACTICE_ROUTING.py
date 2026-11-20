"""Regression tests for direct handling of practical stewardship questions."""
import main as use_main


def test_practical_stewardship_question_is_not_misrouted_to_formation(monkeypatch):
    query = "How can a community practice stewardship in its everyday decisions and responsibilities?"
    monkeypatch.setattr(
        use_main,
        "route_with_model_bank",
        lambda **kwargs: {
            "parsed": {
                "route": "formation",
                "mode": "delegated_journey",
                "confidence": 0.96,
                "reason": "model mistook practice for Formation entry",
                "alternatives": ["guide"],
                "human_reality": "",
                "presenting_situation": "",
                "visitor_proposition": "",
                "underlying_question": "",
                "uncertainty": "",
                "desired_movement": "put stewardship into practice",
                "processing_need": "formation",
                "glossary_term": "",
                "guide_node_id": "",
            },
            "provider": "controlled_test_provider",
            "model": "controlled_test_model",
            "preference_order": [],
        },
    )
    route = use_main._guide_capability_route(query)
    assert route["route"] == "guide"
    assert route["mode"] == "direct"
    assert "direct Guide answer" in route["reason"]


def test_explicit_formation_entry_remains_formation():
    query = "How do I enter the Stewardship Formation pathway?"
    explicit = use_main._explicit_formation_entry_route(query)
    assert explicit is not None
    assert explicit["route"] == "formation"


def test_funding_priority_query_is_not_reclassified_as_practical_stewardship():
    import re
    query = "How should a community decide which of two competing priorities deserves funding when neither can be fully supported?"
    normalized = use_main._normalize_query(query)
    assert not (
        re.search(r"\b(?:practice|practise|everyday|daily|decisions?|responsibilities|community|communities)\b", normalized, re.I)
        and re.search(r"\bstewardship\b", normalized, re.I)
    )


def test_conceptual_trust_role_question_is_not_misclassified_as_practical():
    query = "What is the role of trust in community stewardship?"
    assert use_main._is_conceptual_explanatory_request(query)
    assert not use_main._is_practical_stewardship_question(query)


def test_genuine_practical_stewardship_question_keeps_practical_classification():
    query = "How do I practice stewardship in everyday community decisions?"
    assert not use_main._is_conceptual_explanatory_request(query)
    assert use_main._is_practical_stewardship_question(query)
