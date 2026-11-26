from guide_answerability import is_unjustified_conceptual_abstention


def test_rejects_generic_abstention_for_public_commons_role_question():
    query = "What is the role of public commons in civic renewal?"
    response = (
        "I can't define the role of public commons in civic renewal reliably "
        "from the information available in this response alone."
    )
    assert is_unjustified_conceptual_abstention(query, response)


def test_accepts_a_substantive_general_conceptual_answer():
    query = "What is the role of public commons in civic renewal?"
    response = (
        "Public commons are shared resources and institutions governed for "
        "collective benefit. They support civic renewal by creating places "
        "for participation, cooperation, and accountable shared decisions."
    )
    assert not is_unjustified_conceptual_abstention(query, response)


def test_does_not_override_explicit_source_only_requests():
    query = "What is the role of public commons in civic renewal according to the Living Archive?"
    response = "I can't define this reliably from the information available."
    assert not is_unjustified_conceptual_abstention(query, response)


def test_does_not_override_high_stakes_questions():
    query = "What is the role of legal authority in this case?"
    response = "I can't explain this reliably from the information available."
    assert not is_unjustified_conceptual_abstention(query, response)


def test_does_not_classify_unrelated_nonanswer_as_conceptual_abstention():
    query = "What is the role of public commons in civic renewal?"
    response = "Could you clarify which city or municipality you mean?"
    assert not is_unjustified_conceptual_abstention(query, response)


def test_plural_limits_question_rejects_generic_evidence_abstention():
    query = "What are the limits of self-optimization as a model of development?"
    response = (
        "I can't define The limits of self-optimization as a model of development "
        "reliably from the information available in this response alone."
    )
    assert is_unjustified_conceptual_abstention(query, response)


def test_plural_conceptual_paraphrases_reject_generic_abstention():
    cases = (
        ("What are the risks of optimizing a system around one metric?", "I cannot explain this reliably from the information available."),
        ("What are the boundaries of self-improvement?", "There is not enough information to answer reliably."),
        ("What are the trade-offs of continuous optimization?", "I can't determine the answer from this response alone."),
    )
    for query, response in cases:
        assert is_unjustified_conceptual_abstention(query, response), query


def test_plural_source_only_high_stakes_and_unrelated_questions_stay_excluded():
    refusal = "I cannot explain this reliably from the information available."
    assert not is_unjustified_conceptual_abstention(
        "What are the limits according to the Living Archive only?", refusal
    )
    assert not is_unjustified_conceptual_abstention(
        "What are the risks of this medication?", refusal
    )
    assert not is_unjustified_conceptual_abstention(
        "What are the legal limits of this contract?", refusal
    )
    assert not is_unjustified_conceptual_abstention(
        "What are the opening hours tomorrow?", refusal
    )
