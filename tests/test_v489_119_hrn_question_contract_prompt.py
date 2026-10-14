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


def test_hrn_provider_bank_completes_missing_question_from_grounded_movement_brief():
    partial = {
        "response": (
            "You said you keep putting off a conversation with your friend because "
            "you are afraid the friendship may change. You also described the possibility "
            "that they may feel hurt or pull away, and that things may not be the same. "
            "That leaves the anticipated change in closeness at the center of what you described."
        ),
        "question": "",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }
    messages = [{
        "role": "user",
        "content": (
            "STRUCTURED MOVEMENT BRIEF\n"
            + json.dumps({
                "current_fractal": "I think they may feel hurt or pull away, and then things won't be the same.",
                "thread_summary": "The visitor is postponing a conversation with a friend because they fear the friendship will change.",
                "working_hypothesis": "fear that a conversation will change the friendship",
            })
        ),
    }]

    normalized = provider_bank._normalize_operation_result(
        "hrn_relational", partial, messages=messages
    )
    assert normalized["question"].endswith("?")
    assert "hurt or pull away" in normalized["question"]
    assert provider_bank._hrn_surface_language_violation(normalized["question"]) == ""
    assert provider_bank._hrn_question_grounding_violation(
        normalized["question"], messages
    ) == ""
    assert normalized["response"].startswith("You said you keep putting off")


def test_hrn_provider_bank_replaces_common_advice_sentence_with_grounded_observation():
    partial = {
        "response": (
            "You’re noticing that the team treats the new scope as your responsibility, "
            "while the original deadline feels like a fixed rule that can’t change. "
            "That split in how responsibility is assigned is creating a tension you’re feeling. "
            "It might help to think about ways to honor both the fixed deadline and the fact "
            "that the scope shift is a shared change, rather than a personal burden."
        ),
        "question": "What happens when you bring up the changed scope alongside the agreed deadline?",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }
    messages = [{
        "role": "user",
        "content": (
            "STRUCTURED MOVEMENT BRIEF\\n"
            + json.dumps({
                "observer_contrast": "the changed scope came after the agreed deadline",
                "observer_delta": "the colleague says the effort is too much",
            })
        ),
    }]

    normalized = provider_bank._normalize_operation_result(
        "hrn_relational", partial, messages=messages
    )

    assert "it might help to think about ways" not in normalized["response"].lower()
    assert "changed scope and the agreed deadline" in normalized["response"].lower()
    assert provider_bank._hrn_surface_language_violation(normalized["response"]) == ""
    assert normalized["question"] == partial["question"]


def test_hrn_provider_bank_completes_missing_question_from_agreement_change_evidence():
    partial = {
        "response": (
            "You’re describing a gap between the original agreement and the new work that arrived afterward. "
            "The conversation now seems to be about whether raising that change is reasonable, rather than "
            "how the agreement relates to the work as it stands."
        ),
        "question": "",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }
    messages = [{
        "role": "user",
        "content": (
            "STRUCTURED MOVEMENT BRIEF\\n"
            + json.dumps({
                "observer_contrast": "the original agreement and new work are being treated separately",
                "observer_delta": "the discussion shifts to whether raising the change is reasonable",
                "observer_horizon": "the moment the change in agreement is raised",
            })
        ),
    }]

    normalized = provider_bank._normalize_operation_result(
        "hrn_relational", partial, messages=messages
    )

    assert normalized["question"] == (
        "When you raise what changed in the agreement, what does the other person say or do?"
    )
    assert provider_bank._hrn_surface_language_violation(normalized["question"]) == ""
    assert provider_bank._hrn_question_grounding_violation(
        normalized["question"], messages
    ) == ""


def test_hrn_provider_bank_completes_missing_question_from_scope_change_without_deadline():
    partial = {
        "response": (
            "You are noticing that the new scope has become a personal burden, while the "
            "conversation keeps turning toward whether raising it is reasonable. The changed "
            "work remains part of the agreement, even though the discussion keeps shifting "
            "toward your character instead of the work itself."
        ),
        "question": "",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }
    messages = [{
        "role": "user",
        "content": (
            "STRUCTURED MOVEMENT BRIEF\\n"
            + json.dumps({
                "observer_contrast": "the new scope is being treated as the visitor's responsibility",
                "observer_delta": "the visitor wants to keep commitments honest without being seen as difficult",
                "observer_next_intention": "explore how to name the changed scope in the conversation",
            })
        ),
    }]

    normalized = provider_bank._normalize_operation_result(
        "hrn_relational", partial, messages=messages
    )

    assert normalized["question"] == (
        "When you name the changed scope, what happens in the conversation?"
    )
    assert provider_bank._hrn_surface_language_violation(normalized["question"]) == ""
    assert provider_bank._hrn_question_grounding_violation(
        normalized["question"], messages
    ) == ""


def test_hrn_provider_bank_completes_missing_question_from_deadline_and_new_work():
    partial = {
        "response": (
            "You are describing the strain of carrying new work while the original deadline remains fixed. "
            "When you raise the additional work, the conversation shifts toward whether you are overreacting "
            "instead of acknowledging how the project changed."
        ),
        "question": "",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }
    messages = [{
        "role": "user",
        "content": (
            "STRUCTURED MOVEMENT BRIEF\\n"
            + json.dumps({
                "observer_contrast": "the original deadline remains fixed while new work has been added",
                "observer_delta": "the visitor feels asked to carry both commitments",
                "observer_next_intention": "explore how raising the additional work changes the conversation",
            })
        ),
    }]

    normalized = provider_bank._normalize_operation_result(
        "hrn_relational", partial, messages=messages
    )

    assert normalized["question"] == (
        "When you name the new work alongside the original deadline, what happens in the conversation?"
    )
    assert provider_bank._hrn_surface_language_violation(normalized["question"]) == ""
    assert provider_bank._hrn_question_grounding_violation(
        normalized["question"], messages
    ) == ""


def test_hrn_missing_question_uses_current_visitor_evidence_when_brief_omits_nouns():
    partial = {
        "response": (
            "You are noticing that responsibility feels uneven as the project changes. "
            "The conversation shifts toward whether raising the issue is reasonable, while the new work and original deadline still need to be acknowledged."
        ),
        "question": "",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }
    messages = [
        {
            "role": "system",
            "content": (
                "STRUCTURED MOVEMENT BRIEF\\n"
                + json.dumps({
                    "observer_contrast": "responsibility feels uneven",
                    "observer_delta": "the conversation shifts toward judging the visitor",
                    "observer_next_intention": "explore what changes in the conversation",
                })
            ),
        },
        {
            "role": "user",
            "content": (
                "It feels like I am being asked to carry both the original deadline and the new work, "
                "but when I name the change, the discussion shifts to whether I am overreacting."
            ),
        },
    ]

    normalized = provider_bank._normalize_operation_result(
        "hrn_relational", partial, messages=messages
    )

    assert normalized["question"] == (
        "When you name the new work alongside the original deadline, what happens in the conversation?"
    )
    assert provider_bank._hrn_surface_language_violation(normalized["question"]) == ""
    assert provider_bank._hrn_question_grounding_violation(
        normalized["question"], messages
    ) == ""


def test_hrn_provider_bank_fails_closed_when_missing_question_has_no_grounding():
    partial = {
        "response": (
            "You described a difficult exchange with your friend and wanting to understand "
            "what happens during those conversations. You have not yet shared a concrete "
            "detail that can safely anchor a useful follow-up question."
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


def test_hrn_upstream_brief_failure_does_not_penalize_provider_quality():
    original_state = provider_bank._STATE
    provider_bank._STATE = {
        "models": {},
        "provider_cursor": 0,
        "model_cursors": {},
        "quality": {},
    }
    try:
        reason = (
            "hrn_relational question-surface contract violation: "
            "question-grounding contract violation: structured movement brief is malformed"
        )
        provider_bank._record_quality_rejection("groq", "test-model", "hrn_relational", reason)
        assert provider_bank._quality_state("hrn_relational", "groq", "test-model") == {}
        assert provider_bank._is_movement_brief_input_failure("hrn_relational", reason)
        assert not provider_bank._is_movement_brief_input_failure("generic", reason)
    finally:
        provider_bank._STATE = original_state


def test_hrn_grounding_recovers_valid_prefix_before_malformed_long_context():
    content = (
        "STRUCTURED MOVEMENT BRIEF\\n"
        '{"working_hypothesis":"deadline disagreement",'
        '"thread_summary":"two colleagues disagree about the agreed date",'
        '"underlying_need":"clarity about the date and changed scope",'
        '"current_fractal":"visitor says "the date" is unclear"}'
    )
    messages = [{"role": "user", "content": content}]
    assert provider_bank._hrn_question_grounding_violation(
        "What happens when the agreed date is raised alongside the changed scope?", messages
    ) == ""



def test_hrn_question_grounding_recovers_prefix_before_malformed_perspective_delta():
    content = (
        "STRUCTURED MOVEMENT BRIEF\n"
        '{"working_hypothesis":"deadline disagreement",'
        '"thread_summary":"two colleagues disagree about the agreed date",'
        '"underlying_need":"clarity about the date and added work",'
        '"emerging_delta":"the project scope changed after the original agreement",'
        '"perspective_delta":"The visitor said "we agreed on the date" before the extra work was added",'
        '"body_of_thought":"deadline and changed scope remain in tension"}\n'
        'SOURCE CONTRACT FOR THIS RESPONSE: {"mode":"answer","schema":"v1"}'
    )
    messages = [{"role": "system", "content": content}]
    assert provider_bank._hrn_question_grounding_violation(
        "What happened when the agreed date was discussed alongside the added work?", messages
    ) == ""



def test_hrn_provider_bank_completes_hurt_and_hearing_horizon_without_repeating_tone_question():
    messages = [{
        "role": "user",
        "content": (
            "STRUCTURED MOVEMENT BRIEF\\n"
            + json.dumps({
                "current_fractal": "I wonder whether my hurt can be heard if I cannot explain it perfectly.",
                "thread_summary": "The visitor describes recurring arguments where the original hurt is displaced by defending tone.",
                "working_hypothesis": "The visitor is wondering whether the hurt can be heard without a perfect explanation.",
                "perspective_delta": "From defending how the hurt was explained to wondering whether the hurt itself can be heard.",
                "body_of_thought": "The original hurt gets set aside when the visitor has to explain their tone."
            })
        ),
    }]

    question = provider_bank._hrn_complete_missing_question(messages)

    assert question == "What would tell you that the hurt itself had been heard, even if the explanation were imperfect?"
    assert provider_bank._hrn_surface_language_violation(question) == ""
    assert provider_bank._hrn_question_grounding_violation(question, messages) == ""
