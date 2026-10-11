"""QA for HRN response completion and neutral envelope normalization."""
from provider_bank import _apply_hrn_visitor_contract, _normalize_operation_result, _repair_leading_hrn_hedge


def main():
    messages = [{"role": "system", "content": "Return the required JSON object."}]
    prompt = _apply_hrn_visitor_contract(messages)[0]["content"].casefold()
    assert "two or three complete sentences" in prompt
    assert "240 characters" in prompt
    assert "do not open with hedges" in prompt

    response = (
        "You described feeling unheard when disagreements happen with your friend. "
        "You also said you want to understand the relationship more clearly without "
        "assuming what your friend means or feels. That keeps the focus on what actually "
        "happens between you during disagreement, rather than assigning intentions "
        "that you cannot yet know."
    )
    parsed = {
        "response": response,
        "question": "What do you notice happening just before you begin to feel unheard?",
        "rest": None,
        "use_resource": None,
        "resource_intro": None,
    }
    normalized = _normalize_operation_result("hrn_relational", parsed)
    assert normalized["rest"] is False
    assert normalized["use_resource"] is False
    assert normalized["resource_intro"] == ""

    assert _repair_leading_hrn_hedge(
        "It sounds like the disagreement leaves you feeling unheard."
    ) == "From what you describe, the disagreement leaves you feeling unheard."
    print("V489.99 HRN CONTRACT COMPLETION / ENVELOPE QA: PASS")


if __name__ == "__main__":
    main()
