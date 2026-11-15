import general_guide_composition as composition


QUESTION = "How can economic systems recognize unpaid care and commons maintenance?"


def test_care_and_commons_contract_recovers_policy_enumeration():
    policy_list = (
        "Economic systems can recognize unpaid care and commons maintenance by including them in frameworks and records. "
        "Examples include care credits, tax aggregation, municipal budgets, subsidies, and tax incentives.\n\n"
        "Institutions can formalize recognition through policy tools and participatory structures. "
        "Cooperatives and social impact bonds can also help.\n\n"
        "Finally, metrics and infrastructure funds can support investment in maintenance."
    )
    repaired = composition.enforce_response_contracts(QUESTION, policy_list)
    assert composition._has_care_and_commons_economic_recognition_explanation(repaired)
    assert "conditions that make other economic activity possible" in repaired
    assert "care credits" not in repaired.casefold()


def test_care_contract_does_not_capture_unrelated_economic_question():
    assert not composition._requires_care_and_commons_economic_recognition(
        "How can economic systems improve productivity?"
    )
