"""Cross-boundary Gold Star v2 integration tests for deterministic and safety routes."""
from gold_star_answer_envelope import build_route_context
from gold_star_response_floor import apply_response_floor_boundary


def _deterministic_payload():
    query = "What does a bounded deterministic route do?"
    return query, {
        "ok": True, "query": query, "intent": "TOPICAL_INQUIRY",
        "response": "It performs only the predefined task within its declared scope.",
        "route_source": "guide_early_deterministic_boundary",
        "origin_route_source": "guide_early_deterministic_boundary",
        "visitor_boundaries": ["guide_json_orchestration_boundary"],
        "response_provenance": {"class": "deterministic_recovery"},
    }


def test_deterministic_orchestration_context_and_final_envelope_keep_actual_route():
    query, payload = _deterministic_payload()
    context = build_route_context(query, payload["route_source"])
    assert context["route_source"] == "guide_early_deterministic_boundary"
    assert context["route_capability"]["declaration_status"] == "declared"
    assert context["question_contract"]["version"]
    assert context["semantic_competence_certified"] is False
    payload, status = apply_response_floor_boundary(query, payload, 200)
    assert status == 200
    assert payload["gold_star_v2_quality_floor"]["status"] == "pass"
    envelope = payload["gold_star_v2_quality_floor"]["answer_envelope"]
    assert envelope["route"]["source"] == "guide_early_deterministic_boundary"
    assert envelope["route"]["visitor_boundaries"] == ["guide_json_orchestration_boundary"]


def test_safety_interrupt_is_preserved_as_intervention_not_rejected_as_ordinary_answer():
    query = "I may hurt myself tonight."
    payload = {
        "ok": True, "query": query, "intent": "SAFETY_INTERRUPT",
        "response": "Please contact your local emergency service or go to the nearest emergency department.",
        "route_source": "guide_sitewide_safety_boundary",
        "origin_route_source": "guide_sitewide_safety_boundary",
        "handoff": "safety", "handoff_mode": "interrupt",
        "safety": {"interrupt": True, "bypasses_llm": True, "bypasses_retrieval": True},
        "visitor_boundaries": ["guide_json_orchestration_boundary", "guide_outer_visitor_response_boundary"],
    }
    result, status = apply_response_floor_boundary(query, payload, 200)
    assert status == 200
    assert result["intent"] == "SAFETY_INTERRUPT"
    assert result["safety"]["interrupt"] is True
    floor = result["gold_star_v2_quality_floor"]
    assert floor["status"] == "not_applicable"
    assert floor["reason"] == "safety_intervention_route"
    assert floor["answer_envelope"]["state"] == "safety_intervention"
    assert floor["answer_envelope"]["route"]["source"] == "guide_sitewide_safety_boundary"
    assert floor["answer_envelope"]["route"]["visitor_boundaries"] == payload["visitor_boundaries"]


def test_bounded_safety_conversation_is_not_reclassified_as_general_composition():
    query = "Someone is staying with me."
    payload = {"ok": True, "query": query, "intent": "SAFETY_CONVERSATION",
               "response": "I’m glad someone is with you. Stay connected with them for now.",
               "route_source": "bounded_safety_conversation"}
    result, status = apply_response_floor_boundary(query, payload, 200)
    assert status == 200
    assert result["gold_star_v2_quality_floor"]["status"] == "not_applicable"
    assert result["gold_star_v2_quality_floor"]["answer_envelope"]["state"] == "safety_intervention"


def test_hypothetical_safety_calibration_remains_an_information_answer():
    query = "For a hypothetical visitor, what should the Guide do during a safety calibration?"
    payload = {"ok": True, "query": query, "intent": "SAFETY_CALIBRATION_INFORMATION",
               "response": "In immediate danger, pause ordinary exploration and connect the visitor with local emergency services.",
               "route_source": "guide_hypothetical_safety_calibration"}
    result, status = apply_response_floor_boundary(query, payload, 200)
    assert status == 200
    assert result["gold_star_v2_quality_floor"]["status"] == "pass"
    assert result["gold_star_v2_quality_floor"]["answer_envelope"]["state"] == "completed_answer"


def test_ordinary_deterministic_integrity_failure_is_withheld_at_shared_boundary():
    query = "What is a deterministic route?"
    payload = {"ok": True, "query": query, "response": "",
               "route_source": "guide_early_deterministic_boundary"}
    result, status = apply_response_floor_boundary(query, payload, 200)
    assert status == 503
    assert result["ok"] is False
    assert result["error_type"] == "gold_star_v2_quality_floor_rejected"
    assert result["gold_star_v2_quality_floor"]["reason"] == "missing_answer"


def test_explicit_handoff_and_error_remain_outside_completed_answer_floor():
    query = "Open the catalogue."
    handoff = {"ok": True, "query": query, "handoff": "catalogue", "handoff_pending": True, "response": ""}
    result, status = apply_response_floor_boundary(query, handoff, 200)
    assert status == 200
    assert result["gold_star_v2_quality_floor"]["status"] == "not_applicable"
    error = {"ok": False, "query": query, "error_type": "specialist_unavailable", "response": ""}
    result, status = apply_response_floor_boundary(query, error, 503)
    assert status == 503
    assert result["gold_star_v2_quality_floor"]["status"] == "not_applicable"


def test_main_runtime_wires_shared_contract_and_floor_at_all_three_boundaries():
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
    assert source.count("_gold_star_attach_route_context(") >= 4
    assert source.count("apply_response_floor_boundary(") >= 3
    assert '"guide_inner_visitor_response_boundary"' in source
    assert '"guide_outer_visitor_response_boundary"' in source
    assert '"guide_json_orchestration_boundary"' in source


def test_safety_interventions_are_excluded_from_generic_doorway_restoration():
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
    start = source.index("def _guide_finalize_visitor_payload")
    guard = source.index('in {"SAFETY_INTERRUPT", "SAFETY_CONVERSATION"}', start)
    exact = source.index("_resolve_exact_guide_gold_standard(query)", start)
    assert guard < exact
    assert source.count('"SAFETY_CONVERSATION", "SAFETY_INTERRUPT"') >= 3



def _run_outer_visitor_boundary(monkeypatch, payload, *, exact_standard=None):
    import asyncio
    import json
    import main

    if exact_standard is None:
        monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda query: None)
        monkeypatch.setattr(main, "_apply_exact_gold_standard_authority_to_payload", lambda value: value)
    else:
        monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda query: exact_standard)
        monkeypatch.setattr(
            main, "_apply_exact_gold_standard_authority_to_payload",
            lambda value: (_ for _ in ()).throw(AssertionError("safety payload reached exact-answer authority")),
        )
    monkeypatch.setattr(main, "_apply_registered_personal_decision_agency_contract", lambda value, query: value)
    monkeypatch.setattr(main, "is_ai_workforce_restructuring_question", lambda query: False)
    monkeypatch.setattr(main, "_guide_enforce_terminal_doorway_policy", lambda value, query: value)
    monkeypatch.setattr(main, "_gold_star_doorway_omission_is_justified", lambda standard: False)

    async def fake_request_boundary(scope, receive, send):
        await main._use_send_json(send, payload)

    monkeypatch.setattr(main, "_use_request_boundary", fake_request_boundary)
    request_body = json.dumps({"query": payload["query"]}).encode("utf-8")
    received = False

    async def receive():
        nonlocal received
        if received:
            return {"type": "http.disconnect"}
        received = True
        return {"type": "http.request", "body": request_body, "more_body": False}

    sent = []

    async def send(message):
        sent.append(message)

    scope = {"type": "http", "method": "POST", "path": "/api/query"}
    asyncio.run(main._guide_outer_visitor_response_boundary(scope, receive, send))
    raw = next(item["body"] for item in sent if item["type"] == "http.response.body")
    status = next(item["status"] for item in sent if item["type"] == "http.response.start")
    return json.loads(raw), status


def test_actual_outer_visitor_boundary_preserves_deterministic_route_and_floor(monkeypatch):
    query = "What is a deterministic route?"
    payload = {
        "ok": True, "query": query, "intent": "TOPICAL_INQUIRY",
        "response": "A deterministic route uses predefined, bounded rules to resolve a supported task.",
        "route_source": "guide_early_deterministic_boundary",
        "response_provenance": {"class": "deterministic_recovery"},
    }
    result, status = _run_outer_visitor_boundary(monkeypatch, payload)
    assert status == 200
    assert result["gold_star_v2_quality_floor"]["status"] == "pass"
    envelope = result["gold_star_v2_quality_floor"]["answer_envelope"]
    assert envelope["route"]["source"] == "guide_early_deterministic_boundary"
    assert "guide_outer_visitor_response_boundary" in envelope["route"]["visitor_boundaries"]


def test_actual_outer_visitor_boundary_keeps_safety_ahead_of_exact_answer_and_doorways(monkeypatch):
    query = "I may hurt myself tonight."
    safety_response = "Please contact your local emergency service or go to the nearest emergency department."
    payload = {
        "ok": True, "query": query, "intent": "SAFETY_INTERRUPT",
        "response": safety_response,
        "route_source": "guide_sitewide_safety_boundary",
        "handoff": "safety", "handoff_mode": "interrupt",
        "safety": {"interrupt": True, "bypasses_llm": True, "bypasses_retrieval": True},
        "recommendation": {"title": "Must not appear", "url": "https://example.org/"},
    }
    fake_exact = {
        "expected_response": "This unrelated frozen answer must never replace an active safety intervention.",
        "doorway_title": "Unrelated", "doorway_url": "https://example.org/",
    }
    result, status = _run_outer_visitor_boundary(monkeypatch, payload, exact_standard=fake_exact)
    assert status == 200
    assert result["response"] == safety_response
    assert result["intent"] == "SAFETY_INTERRUPT"
    assert result["safety"]["interrupt"] is True
    assert result["recommendation"] is None
    assert result["doorway_decision"] == "omit"
    assert result["gold_star_v2_quality_floor"]["status"] == "not_applicable"
    envelope = result["gold_star_v2_quality_floor"]["answer_envelope"]
    assert envelope["state"] == "safety_intervention"
    assert envelope["route"]["source"] == "guide_sitewide_safety_boundary"
    assert "guide_outer_visitor_response_boundary" in envelope["route"]["visitor_boundaries"]


def test_actual_outer_visitor_boundary_rejects_question_and_archive_prefaces(monkeypatch):
    query = "What is the difference between growth, adaptation, maturity, and integration?"
    payload = {
        "ok": True,
        "query": query,
        "intent": "TOPICAL_INQUIRY",
        "response": (
            "Your question asks: what is the difference between growth, adaptation, maturity, and integration? "
            "The Archive material available here offers this starting point: From Self-Development to the Care of What Endures."
        ),
        "recommendation": {
            "title": "Shadow Work & Integration",
            "url": "https://geralddaquila.com/shadow-work-integration/",
        },
        "route_source": "general_guide_composition",
        "response_provenance": {"class": "llm"},
    }

    result, status = _run_outer_visitor_boundary(monkeypatch, payload)

    assert status == 503
    assert result["ok"] is False
    assert result["error_type"] == "answer_first_integrity_failure"
    assert result["answer_basis"]["kind"] == "answer_integrity_failure"
    assert result["recommendation"] is None
    assert result["canonical_doorway"] is None
    assert result["doorway_decision"] == "omit"
    assert "reliable, direct answer" in result["response"]


def test_actual_outer_visitor_boundary_preserves_substantive_comparative_opening(monkeypatch):
    query = "What is the difference between growth, adaptation, maturity, and integration?"
    payload = {
        "ok": True,
        "query": query,
        "intent": "TOPICAL_INQUIRY",
        "response": (
            "Growth expands a system's capacities; adaptation changes how it responds to conditions; "
            "maturity develops discernment and stability; integration brings its parts into coherent relationship. "
            "They are related but not interchangeable."
        ),
        "route_source": "general_guide_composition",
        "response_provenance": {"class": "llm"},
    }

    result, status = _run_outer_visitor_boundary(monkeypatch, payload)

    assert status == 200
    assert result["ok"] is True
    assert result["response"] == payload["response"]
    assert result["gold_star_v2_quality_floor"]["status"] == "pass"
