"""Regression guards for outcome-evaluation intent versus FSD diagnosis routing.

These tests protect the Round 1 prompt contract. They do not claim to prove
LLM route choices; that still requires replay against the actual route endpoint.
"""

import main


def test_guide_route_prompt_distinguishes_outcome_evaluation_from_fsd():
    prompt = main._GUIDE_ROUTE_PROMPT.lower()
    assert "distinguish outcome evaluation from systems-pattern diagnosis" in prompt
    assert "observable outcomes" in prompt
    assert "feedback from affected people" in prompt
    assert "unintended or displaced harms" in prompt
    assert "not automatically fsd requests" in prompt


def test_guide_route_prompt_blocks_topic_only_fsd_handoffs():
    prompt = main._GUIDE_ROUTE_PROMPT.lower()
    assert "do not route" in prompt
    assert "solely because the question mentions a group, organization" in prompt
    assert "must not substitute for evaluating outcomes" in prompt
    assert "rather than starting a ten-question diagnostic" in prompt


def test_guide_route_prompt_preserves_legitimate_fsd_use():
    prompt = main._GUIDE_ROUTE_PROMPT.lower()
    assert "fsd is appropriate when the visitor's primary need is to map or diagnose" in prompt
    assert "recurring system patterns" in prompt
    assert "feedback loops" in prompt
    assert "possible leverage points" in prompt


def test_guide_route_prompt_includes_the_observed_calibration_question():
    prompt = main._GUIDE_ROUTE_PROMPT.lower()
    assert "genuinely reducing harm rather than making us feel we addressed it" in prompt
