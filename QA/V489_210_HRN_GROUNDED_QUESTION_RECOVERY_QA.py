"""Regression QA for deterministic recovery of ungrounded HRN questions.

Run from the repository root with:
    python QA/V489_210_HRN_GROUNDED_QUESTION_RECOVERY_QA.py
"""
from provider_bank import _normalize_operation_result


def main():
    response = (
        "You want the hurt to be heard, even when the explanation is not perfect. "
        "Those are not the same as proving what the other person intended, and "
        "the difference remains open in what you have shared."
    )
    original_question = "What does that reveal about the relationship?"
    messages = [
        {
            "role": "user",
            "content": (
                "STRUCTURED MOVEMENT BRIEF\n"
                '{"thread_summary":"You want the hurt to be heard even when your '
                'explanation is imperfect.","working_hypothesis":"The repeated '
                'concern is that the hurt is not being heard."}'
            ),
        }
    ]
    parsed = {
        "response": response,
        "question": original_question,
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }

    result = _normalize_operation_result(
        "hrn_relational", parsed, messages=messages
    )

    assert result["response"] == response, "Recovery must preserve HRN response voice."
    assert result["question"] != original_question, "Ungrounded question was not replaced."
    assert "hurt" in result["question"].casefold(), "Replacement is not grounded in the brief."
    assert result["question"].endswith("?"), "Replacement must remain a question."
    print("PASS: ungrounded HRN question is replaced with a validated grounded question.")


if __name__ == "__main__":
    main()
