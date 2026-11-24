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
