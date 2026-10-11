"""Regression QA for HRN surface-policy alignment at the Provider Bank boundary."""
from provider_bank import _hrn_surface_language_violation, _normalize_operation_result


VALID_RESPONSE = (
    "You described feeling unheard when disagreements happen with your friend. "
    "You also said you want to understand the relationship more clearly without "
    "assuming what your friend means or feels. That keeps the focus on what actually "
    "happens between you during disagreement, rather than assigning intentions "
    "that you cannot yet know."
)

META_ABSTRACT_RESPONSE = (
    "Feeling unheard in disagreement is a specific, observable pattern. "
    "The conversation has clarified one part of the situation without resolving every uncertainty. "
    "The other person's intentions remain unestablished. The exchange can end with the distinction "
    "intact, without turning uncertainty into a verdict."
)


def _parsed(response, question):
    return {
        "response": response,
        "question": question,
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }


def main():
    bad_question = "What could you try to change about how you respond?"
    assert _hrn_surface_language_violation(bad_question)
    normalized = _normalize_operation_result("hrn_relational", _parsed(VALID_RESPONSE, bad_question))
    assert normalized["response"] == VALID_RESPONSE
    assert normalized["question"] == "", "HRN must repair a rejected question without losing valid prose."

    valid_question = "What happens just before you begin to feel unheard?"
    normalized = _normalize_operation_result("hrn_relational", _parsed(VALID_RESPONSE, valid_question))
    assert normalized["question"] == valid_question

    try:
        _normalize_operation_result("hrn_relational", _parsed(META_ABSTRACT_RESPONSE, valid_question))
    except ValueError as exc:
        assert "visitor-surface contract violation" in str(exc)
    else:
        raise AssertionError("Meta-conversational, abstract recovery prose must be rejected upstream.")

    print("V489.101 HRN SURFACE-POLICY BANK ALIGNMENT QA: PASS")


if __name__ == "__main__":
    main()
