"""Regression tests for the shared Guide visitor-facing quality boundary."""


def test_historical_origin_question_cannot_fall_back_to_generic_planning_template():
    import main as app

    query = (
        "On surface, the Philippines is very much a macho society. "
        "Where is the matriarchal reality come from and how it evolved?"
    )
    payload = {
        "ok": True,
        "response": (
            "A practical way to approach On surface, the Philippines is very much a macho society. "
            "Where is the matriarchal reality come from and how it evolved is to define the outcome "
            "you want, identify the main constraint, and choose one step small enough to test. "
            "What detail or context would make this question most concrete for you?"
        ),
        "recommendation": {
            "title": "Is the Philippines Matriarchal or Patriarchal? Understanding Gender Dynamics and Hidden Female Power",
            "url": "https://geralddaquila.com/",
        },
    }

    result = app._guide_finalize_visitor_payload(payload, query)

    assert result["response"] != payload["response"]
    assert "precolonial communities" in result["response"]
    assert "Spanish colonial rule" in result["response"]
    assert len(result["response"].split("\n\n")) == 3
    assert result["recommendation"] == payload["recommendation"]
    assert result["processing"] == "final_visitor_boundary_historical_answer_recovery"


def test_historical_origin_boundary_does_not_rewrite_a_relevant_explanatory_answer():
    import main as app

    query = (
        "On surface, the Philippines is very much a macho society. "
        "Where is the matriarchal reality come from and how it evolved?"
    )
    good_answer = (
        "Women held authority in many precolonial communities, although practices varied.\n\n"
        "Spanish colonial institutions reshaped gender expectations over time, interacting with local customs.\n\n"
        "The present reflects layered histories, so neither 'matriarchal' nor 'patriarchal' alone captures every setting."
    )
    payload = {"ok": True, "response": good_answer, "recommendation": None}

    result = app._guide_finalize_visitor_payload(payload, query)

    assert result is payload


def test_historical_mismatch_detector_matches_actual_visitor_wording():
    import main as app

    query = "On surface, the Philippines is very much a macho society. Where is the matriarchal reality come from and how it evolved?"
    response = "A practical way to approach On surface, the Philippines is very much a macho society. Where is the matriarchal reality come from and how it evolved is to define the outcome you want, identify the main constraint, and choose one step small enough to test."
    assert app._guide_historical_origin_mismatch(query, response) is True


def test_generic_practical_template_is_classified_as_mismatch_for_explanatory_question():
    import main as app

    query = "Where did the matriarchal reality in the Philippines come from and how did it evolve?"
    response = (
        "A practical way to approach this question is to define the outcome you want, "
        "identify the main constraint, and choose one step small enough to test. "
        "What detail or context would make this question most concrete for you?"
    )
    assert app._guide_generic_practical_template_mismatch(query, response) is True


def test_generic_practical_template_remains_available_for_explicit_action_question():
    import main as app

    query = "How do I make a practical plan to resolve a disagreement with my colleague?"
    response = (
        "A practical way to approach this is to define the outcome you want, "
        "identify the main constraint, and choose one step small enough to test."
    )
    assert app._guide_generic_practical_template_mismatch(query, response) is False
