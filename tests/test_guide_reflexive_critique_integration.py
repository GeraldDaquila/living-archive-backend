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
    assert "query," in handler[planner:retrieval]


def test_composer_uses_non_defensive_critique_contract_and_original_question():
    source = Path("general_guide_composition.py").read_text(encoding="utf-8")
    assert 'question_contract.get("institutional_critique", {}).get("detected")' in source
    assert "The visitor is asking you to examine the Living Archive's own worldview" in source
    assert 'f"Visitor question:\\n{question}\\n\\n"' in source


def test_question_contract_keeps_critique_distinct_from_archive_description():
    from gold_star_question_contract import build_question_contract
    critique = build_question_contract("What would constitute a good-faith critique of the Archive’s worldview?")
    description = build_question_contract("What is the Archive’s worldview?")
    assert critique["requested_outcome"] == "critically_examine_archive_worldview"
    assert description["requested_outcome"] == "unresolved"
    assert description["institutional_critique"]["detected"] is False
