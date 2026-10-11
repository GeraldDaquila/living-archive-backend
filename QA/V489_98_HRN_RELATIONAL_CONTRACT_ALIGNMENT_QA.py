"""QA for HRN provider prompt/validator alignment at v489.98."""
from provider_bank import _apply_hrn_visitor_contract, _repair_leading_hrn_hedge


def main():
    messages = [{"role": "system", "content": "Return the required JSON object."}]
    contracted = _apply_hrn_visitor_contract(messages)
    prompt = contracted[0]["content"].casefold()
    assert "two complete sentences" in prompt
    assert "180 characters" in prompt
    assert "do not open with hedges" in prompt

    assert _repair_leading_hrn_hedge(
        "It sounds like the disagreement leaves you feeling unheard."
    ) == "From what you describe, the disagreement leaves you feeling unheard."
    assert _repair_leading_hrn_hedge(
        "It sounds like you feel unheard."
    ) == "From what you describe, you feel unheard."
    assert _repair_leading_hrn_hedge(
        "It seems as though the disagreement is hard to discuss."
    ) == "From what you describe, the disagreement is hard to discuss."
    print("V489.98 HRN RELATIONAL CONTRACT ALIGNMENT QA: PASS")


if __name__ == "__main__":
    main()
