"""Deterministic tests for the HRN JSON question-field contract."""
import pytest

import provider_bank


def test_hrn_provider_prompt_requires_a_separate_nonempty_question_field():
    messages = [{"role": "system", "content": "Return the required JSON object."}]
    guarded = provider_bank._apply_hrn_visitor_contract(messages)
    system = next(item["content"] for item in guarded if item.get("role") == "system")
    normalized = system.lower()

    assert "strict json field contract" in normalized
    assert "question field must never be empty" in normalized
    assert "do not put the follow-up question only inside response" in normalized
    assert "grounded in the visitor's current message" in normalized


def test_hrn_provider_bank_still_rejects_an_empty_question_field():
    partial = {
        "response": (
            "You described trying to explain yourself more when disagreement begins. "
            "You also noticed that this effort leaves you feeling even less heard. "
            "That difference between your intention and what happens next is worth noticing."
        ),
        "question": "",
        "rest": False,
        "use_resource": False,
        "resource_intro": "",
    }

    with pytest.raises(ValueError, match="non-empty question"):
        provider_bank._normalize_operation_result("hrn_relational", partial)
