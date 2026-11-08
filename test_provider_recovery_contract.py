from provider_bank import recovery_contract

def test_hrn_recovery_contract_declares_field_preservation():
    contract=recovery_contract("hrn_relational")
    assert "response" in contract["preserve_on_question_recovery"]
    assert "question" in contract["preserve_on_response_recovery"]
    assert set(contract["hard_failure_fields"]) == {"grounding","safety"}

def test_unknown_operation_has_no_implicit_recovery_contract():
    assert recovery_contract("future_operation") == {}
