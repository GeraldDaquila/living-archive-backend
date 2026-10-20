"""Regression tests for natural HRN specialist routing."""

import main


def test_everyday_stewardship_question_stays_on_the_bounded_guide_path():
    import inspect

    question = (
        "What does stewardship mean in everyday life, and how might it show up "
        "in a person's ordinary responsibilities?"
    )
    assert main._is_practical_stewardship_question(question) is True
    boundary_source = inspect.getsource(main._use_request_boundary)
    practical_guard = boundary_source.find(
        "if _is_practical_stewardship_question(query):"
    )
    macro_gate = boundary_source.find(
        "if not _basic_inquiry_requires_macro_routing(query):"
    )
    assert practical_guard >= 0
    assert macro_gate >= 0
    assert practical_guard < macro_gate


def test_everyday_stewardship_deterministic_answer_does_not_attach_unrelated_archive_resource():
    question = (
        "What does stewardship mean in everyday life, and how might it show up "
        "in a person's ordinary responsibilities?"
    )
    result = main._basic_inquiry_round1_deterministic_response(
        question, {}, {"context_blocks": ""}
    )
    assert "could not verify a sufficiently direct Archive resource" in result["response"]
    assert "keeping a promise" in result["response"]
    assert "At work, it could mean sharing credit fairly" in result["response"]
    assert result["doorway_title"] == ""


def test_friendship_uneven_effort_question_routes_to_hrn():
    question = (
        "I care about a friend, but lately I feel I'm always the one making "
        "an effort. I don't want to judge them unfairly, but I also don't "
        "want to keep ignoring how I feel. How can I understand what's "
        "happening between us?"
    )
    decision = main._relational_boundary_decision(question)
    assert decision["open"] is True
    assert decision["reason"] == "lived_relational_structure"
    assert decision["signals"]["counterpart"] is True
    assert decision["signals"]["dynamic"] is True
    assert decision["signals"]["inquiry"] is True


def test_bounded_resource_lookup_does_not_route_to_hrn():
    question = "Where can I find material about institutional responsibility?"
    decision = main._relational_boundary_decision(question)
    assert decision["open"] is False
    assert decision["reason"] == "bounded_archive_or_definition_request"



def test_credit_taking_in_a_lived_colleague_relationship_opens_hrn_boundary():
    question = (
        "I feel frustrated because my colleague keeps taking credit for work we did together. "
        "What might I be missing about the relationship?"
    )
    decision = main._relational_boundary_decision(question)
    assert decision["open"] is True
    assert decision["reason"] == "lived_relational_structure"
    assert decision["signals"]["first_person"] is True
    assert decision["signals"]["counterpart"] is True
    assert decision["signals"]["dynamic"] is True
    assert decision["signals"]["inquiry"] is True


def test_generic_workplace_credit_taking_question_gets_bounded_answer_without_doorway():
    question = "What are common patterns of taking credit in workplace relationships?"
    result = main._basic_inquiry_round1_deterministic_response(
        question, {}, {"context_blocks": ""}
    )
    assert "presenting shared work as an individual achievement" in result["response"]
    assert "does not establish intent" in result["response"]
    assert result["doorway_title"] == ""
    assert result["provider"] == "bounded_workplace_credit_taking_general_knowledge"


def test_generic_workplace_credit_taking_is_not_confused_with_lived_hrn_case():
    generic = "What are common patterns of taking credit in workplace relationships?"
    lived = "I feel frustrated because my colleague keeps taking credit for work we did together. What might I be missing about the relationship?"
    assert main._is_generic_workplace_credit_taking_question(generic) is True
    assert main._is_generic_workplace_credit_taking_question(lived) is False


def test_generic_question_about_credit_taking_does_not_open_hrn_boundary():
    question = "What are common patterns of taking credit in workplace relationships?"
    decision = main._relational_boundary_decision(question)
    assert decision["open"] is False
    assert decision["reason"] == "insufficient_converging_relational_evidence"


def test_generic_workplace_credit_taking_recognizes_common_general_phrasings():
    general_questions = [
        "What are common patterns of taking credit at work?",
        "What are examples of claiming credit for work in professional relationships?",
        "What are typical patterns of workplace credit?",
    ]
    for question in general_questions:
        assert main._is_generic_workplace_credit_taking_question(question) is True


def test_generic_workplace_credit_taking_excludes_specific_lived_cases():
    lived_questions = [
        "What are common patterns of taking credit at work when my manager keeps taking credit for my work?",
        "What are common patterns of taking credit in workplace relationships when my teammate presents our project as theirs?",
        "What are examples of taking credit at work by someone on my team for my idea?",
        "What are common patterns of taking credit at work? This happened to me last week.",
    ]
    for question in lived_questions:
        assert main._is_generic_workplace_credit_taking_question(question) is False


def test_lived_credit_variants_route_to_hrn_even_when_framed_as_pattern_questions():
    lived_questions = [
        "What are common patterns of taking credit at work when my manager keeps taking credit for my work?",
        "What are common patterns of taking credit in workplace relationships when my teammate presents our project as theirs?",
        "What are examples of taking credit at work by someone on my team for my idea?",
        "What are common patterns of taking credit at work? This happened to me last week.",
    ]
    for question in lived_questions:
        decision = main._relational_boundary_decision(question)
        assert decision["open"] is True
        assert decision["reason"] == "lived_relational_structure"
        assert decision["signals"]["specific_lived_credit"] is True


def test_lived_workplace_credit_omission_routes_to_hrn():
    question = (
        "My teammate presented our project results without mentioning my contribution. "
        "What might I be missing about the relationship?"
    )
    decision = main._relational_boundary_decision(question)
    assert decision["open"] is True
    assert decision["reason"] == "lived_relational_structure"
    assert decision["signals"]["first_person"] is True
    assert decision["signals"]["counterpart"] is True
    assert decision["signals"]["dynamic"] is True
    assert decision["signals"]["inquiry"] is True


def test_reading_list_provider_exhaustion_has_bounded_general_answer_without_doorway():
    question = "What are some ways to organize a personal reading list?"
    result = main._basic_inquiry_round1_deterministic_response(
        question, {}, {"context_blocks": ""}, recommendation_available=False
    )
    assert "one reading list" in result["response"]
    assert "want to read" in result["response"]
    assert result["doorway_title"] == ""
    assert result["provider"] == "bounded_reading_list_recovery"


def test_household_cleaning_schedule_provider_exhaustion_has_bounded_answer_without_doorway():
    question = "How can I make a weekly household cleaning schedule?"
    result = main._basic_inquiry_round1_deterministic_response(
        question, {}, {"context_blocks": ""}, recommendation_available=False
    )
    assert "daily resets" in result["response"]
    assert "two weeks" in result["response"]
    assert result["doorway_title"] == ""
    assert result["provider"] == "bounded_household_schedule_recovery"


def test_generic_friendship_expectations_has_bounded_answer_without_doorway():
    question = "What are common ways people misunderstand expectations in friendships?"
    result = main._basic_inquiry_round1_deterministic_response(
        question, {}, {"context_blocks": ""}, recommendation_available=False
    )
    assert "how often people expect to be in touch" in result["response"]
    assert "unspoken" in result["response"]
    assert result["doorway_title"] == ""
    assert result["provider"] == "bounded_friendship_expectations_recovery"
