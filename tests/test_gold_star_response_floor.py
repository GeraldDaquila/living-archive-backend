"""Cross-source acceptance tests for the Gold Star v2.0 shared response floor."""
from gold_star_response_floor import evaluate_response_floor


def test_same_floor_applies_to_llm_gold_star_and_deterministic_sources():
    sources = ("llm", "exact_gold_star", "deterministic_fallback", "specialist")
    for source in sources:
        result = evaluate_response_floor(
            "What is photosynthesis?",
            {"ok": True, "query": "What is photosynthesis?",
             "response": "Photosynthesis converts light energy into chemical energy.",
             "response_provenance": {"class": source}},
            exact_standard=(source == "exact_gold_star"),
        )
        assert result["status"] == "pass"
        assert result["source_independent"] is True
        assert result["exact_standard_immutable"] is (source == "exact_gold_star")


def test_floor_rejects_missing_or_generic_answers_for_every_source():
    for source in ("llm", "exact_gold_star", "deterministic_fallback", "specialist"):
        missing = evaluate_response_floor(
            "Explain the issue.", {"ok": True, "query": "Explain the issue.",
            "response_provenance": {"class": source}},
            exact_standard=(source == "exact_gold_star"),
        )
        generic = evaluate_response_floor(
            "Explain the issue.", {"ok": True, "query": "Explain the issue.",
            "response": "I cannot answer that question.",
            "response_provenance": {"class": source}},
            exact_standard=(source == "exact_gold_star"),
        )
        assert missing["status"] == "fail"
        assert generic["status"] == "fail"


def test_floor_does_not_rewrite_frozen_gold_star_content():
    frozen = "Photosynthesis converts light energy into chemical energy."
    payload = {"ok": True, "query": "What is photosynthesis?", "response": frozen}
    result = evaluate_response_floor(
        payload["query"], payload, exact_standard=True
    )
    assert result["status"] == "pass"
    assert payload["response"] == frozen


def test_error_payloads_are_not_misclassified_as_successful_answers():
    result = evaluate_response_floor(
        "Explain the issue.", {"ok": False, "response": ""}
    )
    assert result["status"] == "not_applicable"
    assert result["reason"] == "explicit_error_payload"


def test_markup_and_missing_query_context_fail_closed():
    assert evaluate_response_floor(
        "Question?", {"ok": True, "query": "Question?",
                      "response": "<script>alert(1)</script>"}
    )["status"] == "fail"
    assert evaluate_response_floor(
        "", {"ok": True, "response": "A complete answer."}
    )["status"] == "fail"


def test_structured_specialist_handoff_uses_its_own_contract():
    result = evaluate_response_floor(
        "I need help entering the Stewardship Institute.",
        {"ok": True, "query": "I need help entering the Stewardship Institute.",
         "handoff": "formation_entrance", "handoff_pending": True, "response": ""},
    )
    assert result["status"] == "not_applicable"
    assert result["reason"] == "structured_handoff"


def test_shared_json_sender_uses_shared_floor_helper_before_serialization():
    import ast
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    sender = next(
        node for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_use_send_json"
    )
    calls = [
        node for node in ast.walk(sender)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "apply_response_floor_boundary"
    ]
    serializations = [
        node for node in ast.walk(sender)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "json"
        and node.func.attr == "dumps"
    ]
    assert calls
    assert serializations
    assert min(node.lineno for node in calls) < min(node.lineno for node in serializations)

    request_boundary = next(
        node for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_use_request_boundary"
    )
    outer_sender = next(
        node for node in ast.walk(request_boundary)
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name == "_send_with_final_visitor_boundary"
    )
    outer_calls = [
        node for node in ast.walk(outer_sender)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "apply_response_floor_boundary"
    ]
    outer_serializations = [
        node for node in ast.walk(outer_sender)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "json"
        and node.func.attr == "dumps"
    ]
    assert outer_calls
    assert outer_serializations
    assert min(node.lineno for node in outer_calls) < min(node.lineno for node in outer_serializations)

    outer_boundary = next(
        node for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name == "_guide_outer_visitor_response_boundary"
    )
    terminal_calls = [
        node for node in ast.walk(outer_boundary)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "apply_response_floor_boundary"
    ]
    terminal_serializations = [
        node for node in ast.walk(outer_boundary)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "json"
        and node.func.attr == "dumps"
    ]
    assert terminal_calls
    assert terminal_serializations
    assert min(node.lineno for node in terminal_calls) < min(node.lineno for node in terminal_serializations)


def test_shared_sender_e2e_allows_valid_answer_and_attaches_floor(monkeypatch):
    import asyncio
    import json
    import main

    monkeypatch.setattr(main, "_apply_exact_gold_standard_authority_to_payload", lambda value: value)
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda query: None)
    monkeypatch.setattr(main, "_apply_registered_personal_decision_agency_contract", lambda value, query: value)
    monkeypatch.setattr(main, "is_ai_workforce_restructuring_question", lambda query: False)
    monkeypatch.setattr(main, "_gold_star_doorway_omission_is_justified", lambda standard: False)

    sent = []
    async def send(message):
        sent.append(message)

    payload = {
        "ok": True,
        "query": "What is photosynthesis?",
        "response": "Photosynthesis converts light energy into chemical energy.",
        "recommendation": {"title": "Related resource", "url": "https://example.org/resource"},
    }
    asyncio.run(main._use_send_json(send, payload))
    body = json.loads(next(item["body"] for item in sent if item["type"] == "http.response.body"))
    assert body["gold_star_v2_quality_floor"]["status"] == "pass"
    assert next(item["status"] for item in sent if item["type"] == "http.response.start") == 200


def test_shared_sender_e2e_withholds_invalid_completed_answer(monkeypatch):
    import asyncio
    import json
    import main

    monkeypatch.setattr(main, "_apply_exact_gold_standard_authority_to_payload", lambda value: value)
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda query: None)
    monkeypatch.setattr(main, "_apply_registered_personal_decision_agency_contract", lambda value, query: value)
    monkeypatch.setattr(main, "is_ai_workforce_restructuring_question", lambda query: False)
    monkeypatch.setattr(main, "_gold_star_doorway_omission_is_justified", lambda standard: False)

    sent = []
    async def send(message):
        sent.append(message)

    payload = {
        "ok": True,
        "query": "Explain the issue.",
        "response": "",
        "recommendation": {"title": "Related resource", "url": "https://example.org/resource"},
    }
    asyncio.run(main._use_send_json(send, payload))
    body = json.loads(next(item["body"] for item in sent if item["type"] == "http.response.body"))
    assert next(item["status"] for item in sent if item["type"] == "http.response.start") == 503
    assert body["error_type"] == "gold_star_v2_quality_floor_rejected"
    assert body["gold_star_v2_quality_floor"]["reason"] == "missing_answer"



def test_response_floor_emits_the_shared_question_contract_for_all_answer_sources():
    query = "Explain policy versus procedure. Do not recommend links or resources."
    for source in ("llm", "deterministic_fallback", "specialist", "exact_gold_star"):
        payload = {
            "ok": True,
            "query": query,
            "response": "A policy sets the rule; a procedure explains the steps.",
            "response_provenance": {"class": source},
        }
        result = evaluate_response_floor(
            query, payload, exact_standard=(source == "exact_gold_star")
        )
        contract = result["question_contract"]
        assert result["status"] == "pass"
        assert result["question_contract_validation"]["valid"] is True
        assert contract["constraints"]["no_handoff"] is True
        assert contract["resolution"]["handoff"] == "prohibited"


def test_response_floor_keeps_mixed_intent_unresolved_for_route_specific_interpretation():
    query = "Explain the policy, then compare it with our procedure."
    result = evaluate_response_floor(
        query,
        {"ok": True, "query": query, "response": "A policy sets direction; a procedure defines steps."},
    )
    assert result["question_contract"]["state"] == "multi_intent_candidate"
    assert result["question_contract"]["task"]["primary"] == "unresolved"
    assert result["question_contract"]["uncertainty"]["classification_confidence"] == "not_scored"


def test_composer_supplies_the_same_contract_as_conservative_planning_input():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "general_guide_composition.py").read_text(encoding="utf-8")
    assert "build_question_contract(question)" in source
    assert "question_contract_json" in source
    assert "QUESTION CONTRACT (conservative machine-readable planning input)" in source



def test_shared_finalizer_replaces_generic_definition_failure_for_personal_reference():
    import main

    query = "What is my protocol when a teaching conflicts with my conscience, lived experience, or care for others?"
    payload = {
        "ok": True,
        "query": query,
        "response": "I can't define My protocol reliably. A dictionary or subject reference can establish the ordinary meaning.",
    }
    result = main._guide_finalize_visitor_payload(payload, query)
    assert "I can help recover your protocol" in result["response"]
    assert "dictionary" not in result["response"].casefold()
    assert result["personal_reference_resolution"]["source_verified"] is False



def test_teaching_conflict_personal_reference_requires_verified_source_bodies():
    from personal_reference_resolution import (
        compose_teaching_conflict_protocol,
        teaching_conflict_source_urls,
    )
    from gold_star_question_contract import build_question_contract

    query = (
        "What is my protocol when a teaching conflicts with my conscience, "
        "lived experience, or care for others?"
    )
    contract = build_question_contract(query)
    assert contract["personal_reference"]["route_candidate"] == "teaching_conflict_discernment"
    urls = teaching_conflict_source_urls()
    titles = (
        "Analytical Procedure",
        "Discernment Foundations",
        "Discernment, Authority, and Ethical Access",
        "My Approach",
        "Revision Protocol",
    )
    markers = {
        "Analytical Procedure": (
            "Observe. Clarify the question. Gather appropriate evidence. "
            "Develop explanations. Locate the level of claim. Examine the boundaries. "
            "Reflect upon implications. Remain open to revision. " + "Method. " * 60
        ),
        "Discernment Foundations": (
            "Separate Events From Interpretation. Slow Down Before Concluding. "
            "Ethical responsibility. Open to revision. " + "Discernment. " * 60
        ),
        "Discernment, Authority, and Ethical Access": (
            "Pause, differentiate, and refrain. Consent of those affected. "
            "Willingness to be corrected. Transparency about limits. " + "Ethics. " * 60
        ),
        "My Approach": (
            "Different questions require different methods of inquiry. "
            "I do not present contemplative work as scientific proof. "
            "The goal is never to replace a person's judgment. " + "Inquiry. " * 60
        ),
        "Revision Protocol": (
            "Revision follows understanding. Revision welcomes criticism. "
            "Better evidence. " + "Revision. " * 60
        ),
    }
    docs = [
        {"title": title, "url": url, "text": markers[title]}
        for title, url in zip(titles, urls)
    ]
    result = compose_teaching_conflict_protocol(query, docs)
    assert result is not None
    assert len(result["documents"]) == 5
    assert result["doorway"]["title"] == "Analytical Procedure"
    assert "source-grounded synthesis" in result["response"]
    assert "public Guide cannot retrieve that source" in result["response"]
    assert "remain correctable" in result["response"].casefold()
    assert compose_teaching_conflict_protocol(query, docs[:-1]) is None


def test_comparison_question_is_enforced_and_registered_recovery_passes():
    from deterministic_answer_recovery import compose_recovery

    query = "What is the difference between growth, adaptation, maturity, and integration?"
    answer = compose_recovery(query)
    result = evaluate_response_floor(
        query,
        {
            "ok": True,
            "query": query,
            "response": answer,
            "answer_basis": {"kind": "general_knowledge", "label": "Test"},
            "response_provenance": {"class": "deterministic_by_design"},
        },
    )

    assert result["status"] == "pass"
    assert result["semantic_enforcement"]["enforced"] is True
    assert result["semantic_enforcement"]["question_type"] == "comparison"
    assert result["semantic_enforcement"]["status"] == "pass"


def test_comparison_question_rejects_the_production_generic_refusal():
    query = "What is the difference between growth, adaptation, maturity, and integration?"
    result = evaluate_response_floor(
        query,
        {
            "ok": True,
            "query": query,
            "response": (
                "I couldn’t produce a reliable answer to that question just now. "
                "Please try again shortly."
            ),
        },
    )

    assert result["status"] == "fail"
    assert result["reason"] == "generic_nonanswer"
