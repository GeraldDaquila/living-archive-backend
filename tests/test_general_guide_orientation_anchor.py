import general_guide_composition as guide


def test_orientation_anchor_contract_is_part_of_default_guide_system():
    system = guide._GENERAL_GUIDE_SYSTEM
    assert "ORIENTATION-ANCHOR CONTRACT" in system
    assert "recognize the condition → restore a useful distinction or bearing → offer a proportionate next movement" in system


def test_orientation_contract_rejects_generic_decision_first_pattern_for_bearings_query():
    question = (
        "I feel overwhelmed by conflicting information and opinions. "
        "How can I regain my bearings and know what is real enough to act on?"
    )
    generic = (
        "A practical way to approach this is to clarify the outcome and the responsibilities involved. "
        "Identify what is known, which constraints matter, and compare realistic options.\n\n"
        "Next, compare the benefits and harms of each option and consider who is affected.\n\n"
        "Finally, act on the best-supported option and review the consequences."
    )
    assert guide._orientation_anchor_violation(question, generic)


def test_orientation_contract_accepts_response_that_names_the_actual_condition():
    question = (
        "I feel overwhelmed by conflicting information and opinions. "
        "How can I regain my bearings and know what is real enough to act on?"
    )
    oriented = (
        "When everything is competing for your attention, the first problem may not be a lack of information. "
        "It may be a loss of the bearings that help you judge what information deserves your trust.\n\n"
        "A useful distinction is between finding more facts and recovering enough context to weigh them. "
        "Before acting, identify what you can verify, what remains uncertain, and which assumptions are carrying the most weight.\n\n"
        "You do not need perfect certainty before every action. You need a clear enough picture of what is known, what could change your judgment, and what responsibility the next step actually carries."
    )
    assert not guide._orientation_anchor_violation(question, oriented)
