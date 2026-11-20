from guide_reflexive_critique import build_reflexive_critique_plan
from gold_star_question_contract import build_question_contract

def test_good_faith_archive_worldview_critique_is_recognized():
    q = "What would constitute a good-faith critique of the Archive’s worldview?"
    p = build_reflexive_critique_plan(q)
    assert p and p["mode"] == "reflexive_institutional_critique"
    assert p["original_query_preserved"] is True
    assert "independent validation" in p["retrieval_query"]
    assert p["task_class"] == "answer_first_critical_evaluation"
    assert "define_good_faith_critique_in_direct_answer_to_the_visitor" in p["answer_requirements"]
    assert p["response_contract"]["retrieval_role"] == "evidence_for_application_not_a_substitute_for_the_answer"
    c = build_question_contract(q)
    assert c["task"]["primary"] == "institutional_critique_candidate"
    assert c["requested_outcome"] == "critically_examine_archive_worldview"
    assert c["institutional_critique"]["anti_defensiveness_required"] is True

def test_archive_worldview_description_is_not_critique():
    assert build_reflexive_critique_plan("What is the Archive’s worldview?") is None

def test_other_institution_is_not_misclassified():
    assert build_reflexive_critique_plan("What is a good-faith critique of a university’s worldview?") is None

def test_general_worldview_critique_is_not_misclassified():
    assert build_reflexive_critique_plan("What are critiques of a unity worldview?") is None

def test_archive_resource_search_is_not_misclassified():
    assert build_reflexive_critique_plan("Where can I find the Archive’s worldview article?") is None
