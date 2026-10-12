"""Deterministic tests for the HRN JSON question-field contract."""
import json
import pytest

import provider_bank


def test_hrn_provider_prompt_requires_a_separate_nonempty_question_field():
    messages = [{"role": "system", "content": "Return the required JSON object."}]
    guarded = provider_bank._apply_hrn_visitor_contract(messages)
    system = next(item["content"] for item in guarded if item.get("role") == "system")
    normalized = system.lower()

    assert "strict json field contract" in normalized
    assert "question field must never be empty" in normalized
    assert "do not put the follow-up question only inside response" in normalized
    assert "grounded in the structured movement brief" in normalized


def test_hrn_provider_bank_still_rejects_an_empty_question_field():
    partial = {
        "response": (
            "You described trying to explain yourself more when disagreement begins. "
            "You also noticed that this effort leaves you feeling even less heard. "
            "That difference between your intention and what happens next is worth noticing."
        ),
        "question": "",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }

    with pytest.raises(ValueError, match="non-empty question"):
        provider_bank._normalize_operation_result("hrn_relational", partial)


def test_hrn_provider_bank_rejects_a_trailing_question_embedded_in_response():
    partial = {
        "response": (
            "Repeated disagreement can make each person focus on proving what they meant rather than noticing what the other person heard. "
            "The intention may be to clarify, while the effect is that both people feel less understood. "
            "What do you notice about the relationship when you look at that difference?"
        ),
        "question": "What feels most important to understand about the disagreement?",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }

    with pytest.raises(ValueError, match="embedded question"):
        provider_bank._normalize_operation_result("hrn_relational", partial)


def test_hrn_visitor_contract_requires_interaction_grounded_questions():
    messages = [{"role": "system", "content": "Return the required JSON fields."}]
    updated = provider_bank._apply_hrn_visitor_contract(messages)
    contract = updated[0]["content"].lower()

    assert "interaction between the people" in contract
    assert "not merely ask for factual reasons" in contract
    assert "name at least one concrete issue or action from the actual fields" in contract
    assert "unless the actual issue is named" in contract
    assert "the raw visitor message may not be available" in contract


def test_hrn_provider_bank_rejects_generic_distinction_question():
    assert provider_bank._hrn_surface_language_violation(
        "What changes when you look at the situation through that distinction?"
    ) == "formulaic-abstract-question"


def test_hrn_provider_bank_rejects_solution_framing_in_response():
    assert provider_bank._hrn_surface_language_violation(
        "This is opening the possibility to negotiate which element should be the negotiable anchor."
    ) == "action-solution-frame"



def test_hrn_question_grounding_rejects_generic_question_without_brief_anchor():
    brief = {
    "working_hypothesis": "deadline disagreement",
    "thread_summary": "two colleagues disagree about the agreed date",
    "underlying_need": "shared clarity about the date and added work",
    "emerging_delta": "the project scope changed after the original agreement",
    "body_of_thought": "deadline and changed scope remain in tension"
}
    messages = [
        {"role": "system", "content": "Write one response and one question."},
        {"role": "user", "content": "STRUCTURED MOVEMENT BRIEF\\n" + json.dumps(brief) + "\\n\\nSHARED RELATIONAL UNDERSTANDING"},
    ]
    generic = "What does that reveal about the relationship?"
    grounded = "What happens when the agreed date is raised alongside the changed scope?"
    assert provider_bank._hrn_question_grounding_violation(generic, messages).startswith("question-grounding contract violation")
    assert provider_bank._hrn_question_grounding_violation(grounded, messages) == ""


def test_hrn_question_grounding_rejects_abstract_distinction_only():
    messages = [{
        "role": "user",
        "content": "STRUCTURED MOVEMENT BRIEF\\n" + json.dumps({
            "working_hypothesis": "deadline distinction",
            "underlying_need": "clarity about the date and changed scope",
        }),
    }]
    violation = provider_bank._hrn_question_grounding_violation("What changes when you look through that distinction?", messages)
    assert violation.startswith("question-grounding contract violation")


def test_hrn_question_grounding_finds_brief_in_system_message():
    messages = [{
        "role": "system",
        "content": "STRUCTURED MOVEMENT BRIEF\\n" + json.dumps({
    "working_hypothesis": "deadline disagreement",
    "thread_summary": "two colleagues disagree about the agreed date",
    "underlying_need": "shared clarity about the date and added work",
    "emerging_delta": "the project scope changed after the original agreement",
    "body_of_thought": "deadline and changed scope remain in tension"
}),
    }]
    generic = "Where do you notice that distinction most clearly in the relationship?"
    grounded = "What happens in their conversation when the deadline is raised alongside the changed scope?"
    assert provider_bank._hrn_question_grounding_violation(generic, messages).startswith("question-grounding contract violation")
    assert provider_bank._hrn_question_grounding_violation(grounded, messages) == ""


def test_hrn_question_grounding_fails_closed_when_brief_is_missing_or_malformed():
    missing = [{"role": "system", "content": "Return a separate response and question."}]
    malformed = [{"role": "system", "content": "STRUCTURED MOVEMENT BRIEF: no structured object"}]
    question = "What happens in their conversation when the agreed date is raised?"
    assert provider_bank._hrn_question_grounding_violation(question, missing).startswith(
        "question-grounding contract violation"
    )
    assert provider_bank._hrn_question_grounding_violation(question, malformed).startswith(
        "question-grounding contract violation"
    )


def test_hrn_provider_bank_rejects_observed_reallocation_and_negotiation_guidance():
    response = (
        "One colleague is anchoring to the original deadline, while the other is pulling the goalpost "
        "by emphasizing a changed scope of work. Seeing the clash as a shift in what each person regards "
        "as the agreed task, rather than just a timing dispute, opens space to renegotiate expectations "
        "and align on what truly needs to be delivered."
    )
    assert provider_bank._hrn_surface_language_violation(response) == "action-guidance"


def test_hrn_question_grounding_parses_raw_line_breaks_inside_visitor_brief():
    raw_brief = (
        "STRUCTURED MOVEMENT BRIEF\n"
        '{"working_hypothesis":"deadline disagreement",'
        '"thread_summary":"colleague A holds the agreed deadline\n'
        'colleague B cites changed scope",'
        '"underlying_need":"clarity about the deadline and scope"}'
    )
    messages = [{"role": "user", "content": raw_brief}]
    assert provider_bank._hrn_question_grounding_violation(
        "What happens when the agreed deadline is raised alongside the changed scope?", messages
    ) == ""


def test_hrn_question_grounding_recovers_double_escaped_brief():
    brief = {
        "working_hypothesis": "deadline disagreement",
        "thread_summary": "two colleagues disagree about the agreed date",
        "underlying_need": "clarity about the date and changed scope",
    }
    double_encoded = json.dumps(json.dumps(brief))
    messages = [{"role": "user", "content": "STRUCTURED MOVEMENT BRIEF\\n" + double_encoded}]
    assert provider_bank._hrn_question_grounding_violation(
        "What happens when the agreed date is raised alongside the changed scope?", messages
    ) == ""
