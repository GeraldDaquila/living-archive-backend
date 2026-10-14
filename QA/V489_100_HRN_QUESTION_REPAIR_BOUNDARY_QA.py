"""Regression QA for HRN question quality at the Provider Bank boundary."""
from provider_bank import _hrn_surface_language_violation, _normalize_operation_result


VALID_RESPONSE = (
    "You described feeling unheard when disagreements happen with your friend. "
    "You also said you want to understand the relationship more clearly without "
    "assuming what your friend means or feels. That keeps the focus on what actually "
    "happens between you during disagreement, rather than assigning intentions "
    "that you cannot yet know."
)


def _parsed(question):
    return {
        "response": VALID_RESPONSE,
        "question": question,
        "rest": None,
        "use_resource": None,
        "resource_intro": None,
    }


def main():
    prescriptive = "What could you try to change about how you respond?"
    assert _hrn_surface_language_violation(prescriptive)

    try:
        _normalize_operation_result("hrn_relational", _parsed(prescriptive))
    except ValueError as exc:
        assert "question-surface contract violation" in str(exc)
    else:
        raise AssertionError(
            "A prescriptive HRN question must be rejected before the bridge."
        )

    try:
        _normalize_operation_result("hrn_relational", _parsed(None))
    except ValueError as exc:
        assert "non-empty question" in str(exc)
    else:
        raise AssertionError(
            "A missing question must be rejected and routed to an independent provider."
        )

    # A provider-authored abstract question must be repaired only when the
    # structured movement brief supplies a concrete, validated focus.
    movement_messages = [
        {
            "role": "user",
            "content": (
                "STRUCTURED MOVEMENT BRIEF\\n"
                '{"thread_summary":"You want the hurt to be heard even when your '
                'explanation is imperfect.","working_hypothesis":"The repeated '
                'concern is that the hurt is not being heard."}'
            ),
        }
    ]
    grounded = _normalize_operation_result(
        "hrn_relational",
        _parsed("What does that reveal about the relationship?"),
        messages=movement_messages,
    )
    assert grounded["response"] == VALID_RESPONSE
    assert grounded["question"] != "What does that reveal about the relationship?"
    assert "hurt" in grounded["question"].casefold()
    assert grounded["question"].endswith("?")

    valid_question = "What happens just before you begin to feel unheard?"
    preserved = _normalize_operation_result("hrn_relational", _parsed(valid_question))
    assert preserved["question"] == valid_question
    assert preserved["rest"] is False
    assert preserved["use_resource"] is False
    assert preserved["resource_intro"] == ""

    short = _parsed(valid_question)
    short["response"] = "You feel unheard. That is difficult."
    try:
        _normalize_operation_result("hrn_relational", short)
    except ValueError as exc:
        assert "response shape" in str(exc)
    else:
        raise AssertionError("Invalid response prose must still be rejected by the Provider Bank.")

    print("V489.117 HRN QUESTION QUALITY BOUNDARY QA: PASS")


if __name__ == "__main__":
    main()
