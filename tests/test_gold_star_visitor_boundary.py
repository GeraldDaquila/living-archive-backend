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
