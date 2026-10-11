"""Regression QA for HRN question-repair ownership at the Provider Bank boundary."""
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

    normalized = _normalize_operation_result("hrn_relational", _parsed(prescriptive))
    assert normalized["response"] == VALID_RESPONSE
    assert normalized["question"] == "", "HRN must receive the valid response and repair the question locally."
    assert normalized["rest"] is False
    assert normalized["use_resource"] is False
    assert normalized["resource_intro"] == ""

    missing = _normalize_operation_result("hrn_relational", _parsed(None))
    assert missing["response"] == VALID_RESPONSE
    assert missing["question"] == "", "Missing questions must defer to HRN structural completion."

    valid_question = "What happens just before you begin to feel unheard?"
    preserved = _normalize_operation_result("hrn_relational", _parsed(valid_question))
    assert preserved["question"] == valid_question

    short = _parsed(valid_question)
    short["response"] = "You feel unheard. That is difficult."
    try:
        _normalize_operation_result("hrn_relational", short)
    except ValueError as exc:
        assert "response shape" in str(exc)
    else:
        raise AssertionError("Invalid response prose must still be rejected by the Provider Bank.")

    print("V489.100 HRN QUESTION REPAIR BOUNDARY QA: PASS")


if __name__ == "__main__":
    main()
