"""Regression tests for HRN movement-brief extraction at the provider boundary."""

from provider_bank import _hrn_question_grounding_violation


def test_grounding_validator_skips_source_contract_after_instruction_marker():
    messages = [
        {
            "role": "system",
            "content": (
                'The structured movement brief is the only representation available. '
                'SOURCE CONTRACT FOR THIS RESPONSE: {"mode":"answer","schema":"v1"}'
            ),
        },
        {
            "role": "user",
            "content": (
                'STRUCTURED MOVEMENT BRIEF — compose from this interpretation:\n'
                '{"thread_summary":"The original estimate did not include the added work.",'
                '"working_hypothesis":"The deadline expectation rested on an incomplete estimate.",'
                '"perspective_delta":"The original estimate excluded the added work."}'
            ),
        },
    ]
    violation = _hrn_question_grounding_violation(
        "What changed in the original estimate?",
        messages,
    )
    assert violation == ""


def test_grounding_validator_fails_closed_when_no_semantic_brief_exists():
    messages = [
        {
            "role": "system",
            "content": 'STRUCTURED MOVEMENT BRIEF then SOURCE CONTRACT: {"mode":"answer","schema":"v1"}',
        },
    ]
    violation = _hrn_question_grounding_violation("What changed?", messages)
    assert violation in {
        "question-grounding contract violation: structured movement brief is missing",
        "question-grounding contract violation: structured movement brief is malformed",
        "question-grounding contract violation: movement brief has no concrete question anchors",
    }
