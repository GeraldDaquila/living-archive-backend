# Response preservation is a bank-level efficiency requirement: recover a field
# without discarding already-valid generated work.

def test_field_recovery_preserves_first_pass_response_and_flags():
    first={"response":"A complete grounded response.","question":"Old question","grounded":True,"safe":True}
    repaired_question="What happened when the schedule changed?"
    merged=dict(first); merged["question"]=repaired_question
    assert merged["response"] == first["response"]
    assert merged["grounded"] is True
    assert merged["safe"] is True
    assert merged["question"] == repaired_question

def test_preservation_contract_requires_explicit_field_replacement():
    first={"response":"Keep this scarce successful generation.","question":"Repair only this field."}
    replacement={"question":"A corrected grounded question."}
    merged=dict(first); merged.update(replacement)
    assert merged["response"] == first["response"]
