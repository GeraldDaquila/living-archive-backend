from pathlib import Path


def test_reflexive_critique_plan_is_applied_before_canonical_retrieval():
    source = Path("main.py").read_text(encoding="utf-8")
    start = source.index("def _basic_inquiry_response(query")
    end = source.index("\ndef _v48831_basic_inquiry_seam_self_audit", start)
    handler = source[start:end]
    planner = handler.index("_reflexive_critique_plan = _build_reflexive_critique_plan(query)")
    retrieval = handler.index("context_data = use_core.fetch_canonical_context(resource_query)")
    assert planner < retrieval
    assert 'resource_query = _reflexive_critique_plan["retrieval_query"]' in handler
    assert "query" in handler[planner:retrieval]


def test_composer_uses_non_defensive_critique_contract_and_original_question():
    source = Path("general_guide_composition.py").read_text(encoding="utf-8")
    assert 'question_contract.get("institutional_critique", {}).get("detected")' in source
    assert "The visitor is asking you to examine the Living Archive's own worldview" in source
    assert r'f"Visitor question:\n{question}\n\n"' in source


def test_question_contract_keeps_critique_distinct_from_archive_description():
    from gold_star_question_contract import build_question_contract
    critique = build_question_contract("What would constitute a good-faith critique of the Archive’s worldview?")
    description = build_question_contract("What is the Archive’s worldview?")
    assert critique["requested_outcome"] == "critically_examine_archive_worldview"
    assert description["requested_outcome"] == "unresolved"
    assert description["institutional_critique"]["detected"] is False

 
def test_first_class_critique_plan_survives_retrieval_and_composition():
    main = Path("main.py").read_text(encoding="utf-8")
    composition = Path("general_guide_composition.py").read_text(encoding="utf-8")
    assert 'context_data["_reflexive_institutional_critique"] = _reflexive_critique_plan' in main
    assert "answer_first=true" in main
    assert "REFLEXIVE CRITIQUE ANSWER-FIRST CONTRACT" in composition
    assert "A retrieved passage is evidence to analyze, never the answer by itself" in composition
    assert "Never respond by quoting or paraphrasing one Archive passage and then saying no resource was found" in composition


def test_reflexive_critique_plan_requires_a_direct_answer_even_with_no_sources():
    from guide_reflexive_critique import build_reflexive_critique_plan
    plan = build_reflexive_critique_plan("What would constitute a good-faith critique of the Archive’s worldview?")
    assert plan["response_contract"]["fallback"] == "answer_the_general_methodological_question_and_bound_archive_specific_claims"
    assert "offer_no_doorway_unless_existing_canonical_authority_and_relevance_gates_pass" in plan["answer_requirements"]

def test_reflexive_critique_cannot_be_overwritten_by_subject_discovery():
    source = Path("main.py").read_text(encoding="utf-8")
    start = source.index("def _basic_inquiry_response(query")
    end = source.index("\\ndef _v48831_basic_inquiry_seam_self_audit", start)
    handler = source[start:end]
    plan = handler.index("_reflexive_critique_plan = _build_reflexive_critique_plan(query)")
    suppress = handler.index("discovery_subject = \"\"", plan)
    discovery_override = handler.index("if discovery_subject:", suppress)
    assert plan < suppress < discovery_override
    assert "resource_summary_override=false" in handler[suppress:discovery_override]
    assert "if discovery_subject:" in handler[discovery_override:]


def test_critique_retrieval_targets_foundational_archive_claims():
    from guide_reflexive_critique import build_reflexive_critique_plan
    plan = build_reflexive_critique_plan(
        "What would constitute a good-faith critique of the Archive’s worldview?"
    )
    query = plan["retrieval_query"].casefold()
    assert "sensemaking infrastructure" in query
    assert "constitutional or cornerstone texts" in query
    assert "exclude unrelated applied examples" in query
    assert "methodological answer" in query
