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
