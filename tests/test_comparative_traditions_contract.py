import comparative_traditions_contract as contract


QUESTION = "How can multiple spiritual traditions be approached with respect and intellectual discipline?"


def test_detects_plural_spiritual_tradition_approach_question():
    assert contract.is_comparative_traditions_question(QUESTION)


def test_rejects_institutional_decision_substitution_from_visitor_example():
    response = (
        "The inquiry begins by making the situation itself visible: multiple "
        "spiritual traditions are approached with respect and intellectual "
        "discipline. What outcome is the organisation trying to achieve, what "
        "responsibilities does it carry, and who will live with the consequences? "
        "Those questions bring operations, governance, human development, ethics, "
        "and stewardship into the same frame.\n\n"
        "From there, compare the real options rather than assuming that the "
        "proposed course is the only one. Look at what each option makes possible, "
        "what it may damage, who bears the costs, and what evidence would justify "
        "changing direction.\n\n"
        "The point is not to make the decision for the organisation, but to make "
        "the grounds for acting clearer."
    )
    assert contract.response_substitutes_institutional_frame(QUESTION, response)


def test_preserves_genuinely_comparative_response():
    response = (
        "Approach each tradition on its own terms, attending to its history, "
        "practitioners, sources, beliefs, and practices.\n\n"
        "Distinguish historical, philosophical, empirical, and experiential "
        "claims, and examine each with methods suited to the claim.\n\n"
        "Compare carefully without flattening differences, and acknowledge "
        "uncertainty and the limits of your own standpoint."
    )
    assert not contract.response_substitutes_institutional_frame(QUESTION, response)


def test_does_not_trigger_for_institutional_question():
    question = "How should an organisation compare governance options?"
    response = "Compare the decisions, costs, responsibilities, and consequences."
    assert not contract.response_substitutes_institutional_frame(question, response)


def test_recovery_is_three_paragraphs_and_covers_epistemic_distinctions():
    response = contract.recovery_response()
    assert len(response.split("\\n\\n")) == 3
    for term in ("historical", "philosophical", "empirical", "spiritual experience"):
        assert term in response.lower()
