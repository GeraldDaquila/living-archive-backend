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
    assert len(response.split("\n\n")) == 3
    for term in ("historical", "philosophical", "empirical", "spiritual experience"):
        assert term in response.lower()


def test_verified_doorway_matches_comparative_inquiry_and_is_public_archive_asset():
    doorway = contract.verified_doorway(QUESTION)
    assert doorway == {
        "title": "At the Edge of Explanation",
        "url": "https://geralddaquila.com/2026/07/20/at-the-edge-of-explanation/",
    }


def test_verified_doorway_fails_closed_for_unrelated_questions():
    assert contract.verified_doorway("How should an organisation redesign governance?") is None

def test_valid_comparative_answer_still_has_verified_doorway():
    response = (
        "Approach each tradition on its own terms, attending to its history, "
        "practitioners, sources, beliefs, and practices.\n\n"
        "Distinguish historical, philosophical, empirical, and experiential "
        "claims, and examine each with methods suited to the claim.\n\n"
        "Compare carefully without flattening differences, and acknowledge "
        "uncertainty and the limits of your own standpoint."
    )
    assert not contract.response_substitutes_institutional_frame(QUESTION, response)
    assert contract.verified_doorway(QUESTION) == {
        "title": "At the Edge of Explanation",
        "url": "https://geralddaquila.com/2026/07/20/at-the-edge-of-explanation/",
    }


def test_detects_named_religions_in_explicit_similarity_difference_question():
    question = "What are the similarities and differences between Buddhism, Christianity and Islam?"
    assert contract.is_comparative_traditions_question(question)
    assert contract.verified_doorway(question) == {
        "title": "At the Edge of Explanation",
        "url": "https://geralddaquila.com/2026/07/20/at-the-edge-of-explanation/",
    }


def test_detects_named_religions_in_comparison_wording():
    question = "Compare Buddhism, Christianity and Islam as spiritual paths."
    assert contract.is_comparative_traditions_question(question)


def test_named_religions_without_plural_comparison_intent_do_not_trigger():
    question = "What is the history of Buddhism?"
    assert not contract.is_comparative_traditions_question(question)
    assert contract.verified_doorway(question) is None


def test_governance_control_still_fails_closed():
    question = "How should an organisation assign responsibilities and consequences when redesigning its governance process?"
    assert not contract.is_comparative_traditions_question(question)
    assert contract.verified_doorway(question) is None


def test_detects_reductive_universal_claims_and_repairs_them():
    response = "All three religions teach compassion and share a focus on the afterlife. Their differences are mainly cultural."
    assert contract.response_flattens_traditions(QUESTION, response)
    assert contract.response_requires_quality_repair(QUESTION, response)


def test_gold_star_recovery_preserves_internal_diversity_and_epistemic_fit():
    response = contract.recovery_response()
    assert len(response.split("\n\n")) == 3
    for phrase in ("internal differences", "historical evidence", "philosophical and theological", "false equivalence", "practitioners"):
        assert phrase in response.lower()
    assert not contract.response_requires_quality_repair(QUESTION, response)


def test_quality_repair_does_not_trigger_on_unrelated_governance_question():
    question = "How should an organisation compare governance options?"
    response = "All three governance options share a focus on accountability."
    assert not contract.response_requires_quality_repair(question, response)


def test_recovery_never_claims_all_traditions_share_one_doctrine():
    response = contract.recovery_response().lower()
    assert "all traditions believe" not in response
    assert "all three religions" not in response
    assert "false equivalence" in response


def test_detects_all_three_teach_claim_in_named_religion_comparison():
    question = "What are the similarities and differences between Buddhism, Christianity and Islam?"
    response = (
        "All three teach compassion and encourage followers to live ethically. "
        "They also share a focus on the afterlife."
    )
    assert contract.is_comparative_traditions_question(question)
    assert contract.response_flattens_traditions(question, response)
    assert contract.response_requires_quality_repair(question, response)
