from provider_contract_diagnostics import contract_reason_code


def test_three_paragraph_rejection_has_specific_stable_code():
    reason = "substantive explanatory answer must meet the three-paragraph Guide Gold Standard"
    assert contract_reason_code(reason) == "three_paragraph_minimum"


def test_question_specific_quality_rejections_are_distinguished():
    assert contract_reason_code(
        "outcome-evaluation answer must include observable evidence, comparison, and a countercheck"
    ) == "outcome_evaluation_coverage"
    assert contract_reason_code(
        "explicit follow-up invitation request requires a closing question"
    ) == "closing_question_missing"


def test_shape_and_privacy_failures_have_distinct_codes():
    assert contract_reason_code("general composition response is too short") == "response_too_short"
    assert contract_reason_code("general composition exposed internal implementation language") == "internal_language_exposure"


def test_unknown_contract_messages_fail_closed_to_bounded_code():
    assert contract_reason_code("visitor prompt or generated answer must never appear here") == "unclassified_contract"


def test_reason_code_output_never_contains_raw_message():
    raw = "substantive explanatory answer must meet the three-paragraph Guide Gold Standard"
    code = contract_reason_code(raw)
    assert code == "three_paragraph_minimum"
    assert raw not in code
