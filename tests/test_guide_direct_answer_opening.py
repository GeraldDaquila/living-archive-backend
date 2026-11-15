"""Regression coverage for direct-answer opening discipline."""
import general_guide_composition as composition


def test_direct_answer_contract_forbids_question_categorization_openers():
    contract = composition._GENERAL_GUIDE_SYSTEM
    assert 'Do not open by restating or categorizing the visitor' in contract
    assert '"For a question like..."' in contract
    assert 'make the first sentence itself a direct claim' in contract
