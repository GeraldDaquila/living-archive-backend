"""Regression tests for practical next-step composition guidance."""

import general_guide_composition as composition


def test_practical_next_step_contract_answers_before_optional_context():
    instruction = (
        "For practical questions asking for a constructive next step, how to begin, "
        "or what a group should do when members disagree, give one useful, low-risk "
        "next step before asking for more context when general guidance is responsible."
    )
    assert instruction in composition._GENERAL_GUIDE_SYSTEM
    assert "Ask for context only when its absence materially changes" in composition._GENERAL_GUIDE_SYSTEM
    assert "make any follow-up question optional after the useful answer" in composition._GENERAL_GUIDE_SYSTEM


def test_practical_guidance_preserves_agency_and_avoids_mandatory_checklists():
    system = composition._GENERAL_GUIDE_SYSTEM
    assert "Do not present these as a mandatory checklist" in system
    assert "Do not claim this will resolve the conflict or assume facts about the group" in system


def test_practical_next_step_rule_preserves_distress_pacing_exception():
    system = composition._GENERAL_GUIDE_SYSTEM
    practical_rule = system.index("For practical questions asking for a constructive next step")
    distress_rule = system.index("When a visitor discloses grief or significant distress")
    assert practical_rule < distress_rule
    assert "does not override safety boundaries" in system
    assert "special pacing required for grief and significant distress" in system



def test_practical_next_step_question_is_detected():
    query = (
        "If the group agrees that something must change but its members disagree "
        "about what to do first, what would be a constructive next step?"
    )
    assert composition._requires_actionable_next_step(query)


def test_analysis_only_response_is_rejected_for_practical_next_step_question():
    query = (
        "If the group agrees that something must change but its members disagree "
        "about what to do first, what would be a constructive next step?"
    )
    parse = composition._parse_factory(
        [{"title": "Collective Sense-making SOP", "url": "https://example.test", "content": "Consensus."}],
        query,
    )
    import json
    analysis_only = json.dumps({
        "response": (
            "The group should identify the claim at issue, separate facts from "
            "assumptions, and examine what evidence would distinguish explanations. "
            "I need more context to offer a case-specific conclusion."
        ),
        "response_shape": "general",
        "doorway_title": "",
    })
    try:
        parse(analysis_only)
    except ValueError as exc:
        assert "one concrete action" in str(exc)
    else:
        raise AssertionError("analysis-only response should be rejected")


def test_concrete_action_response_passes_practical_next_step_validation():
    query = (
        "If the group agrees that something must change but its members disagree "
        "about what to do first, what would be a constructive next step?"
    )
    parse = composition._parse_factory([], query)
    import json
    actionable = json.dumps({
        "response": (
            "Ask each person to explain what they believe is most urgent and why. "
            "Then identify the shared goal and agree on one small, reversible action "
            "the group can try together."
        ),
        "response_shape": "general",
        "doorway_title": "",
    })
    result = parse(actionable)
    assert "Ask each person" in result["response"]



def test_final_recovery_replaces_analysis_only_answer_with_action():
    query = (
        "If the group agrees that something must change but its members disagree "
        "about what to do first, what would be a constructive next step?"
    )
    analysis_only = (
        "The group should identify the claim at issue, separate facts from assumptions, "
        "and examine what evidence would distinguish plausible explanations. "
        "I don't have enough verified context to assert a case-specific conclusion."
    )
    result = composition.enforce_actionable_next_step(query, analysis_only)
    assert result != analysis_only
    assert composition._has_concrete_next_step(result)
    assert "Ask each person" in result


def test_final_recovery_preserves_already_actionable_answer():
    query = (
        "If the group agrees that something must change but its members disagree "
        "about what to do first, what would be a constructive next step?"
    )
    actionable = (
        "Ask each person to explain what they believe is most urgent and why. "
        "Then agree on one small action the group can try together."
    )
    assert composition.enforce_actionable_next_step(query, actionable) == actionable


def test_final_recovery_does_not_rewrite_unrelated_questions():
    query = "Why does collective sense-making matter?"
    response = "Collective sense-making helps people compare perspectives and understand a shared situation."
    assert composition.enforce_actionable_next_step(query, response) == response
