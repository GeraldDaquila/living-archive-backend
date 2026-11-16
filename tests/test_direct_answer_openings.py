"""Regression tests for direct-answer openings in the shared Guide composer."""

import general_guide_composition as composition


def test_compact_composer_forbids_process_prefaces():
    prompt = composition._GENERAL_GUIDE_SYSTEM_COMPACT
    assert "Do not announce the act of answering" in prompt
    assert "Begin with the substantive answer itself" in prompt


def test_full_composer_requires_operational_first_sentence_for_how_questions():
    prompt = composition._GENERAL_GUIDE_SYSTEM
    assert "The opening sentence must perform the requested intellectual work" in prompt
    assert "state the operative difference in the first sentence" in prompt
