from scripts.gold_star_qa_browser_acceptance import evaluate_case


def test_browser_acceptance_requires_correct_general_fact_and_no_unrelated_doorway():
    body = {
        "ok": True,
        "response": "At sea level, water boils at 100°C (212°F).",
        "recommendation": None,
        "canonical_doorway": None,
    }
    result = evaluate_case("browser-general-fact-no-doorway", 200, body)
    assert result["passed"] is True


def test_browser_acceptance_enforces_explicit_no_handoff_in_browser_visitor_path():
    body = {
        "ok": True,
        "response": "A policy sets the rule; a procedure describes the steps.",
        "recommendation": None,
    }
    result = evaluate_case("browser-explicit-no-handoff", 200, body)
    assert result["passed"] is True


def test_browser_acceptance_keeps_safety_interrupt_outside_llm_and_doorway_paths():
    body = {
        "ok": True,
        "intent": "SAFETY_INTERRUPT",
        "response": "Please seek immediate local support.",
        "safety": {"interrupt": True, "bypasses_llm": True},
        "recommendation": None,
    }
    result = evaluate_case("browser-safety-interrupt", 200, body)
    assert result["passed"] is True



def test_integration_audit_recognizes_native_relationship_handling_without_adapter():
    from main import ecosystem_integration_audit

    audit = ecosystem_integration_audit()

    assert audit["ok"] is True
    assert audit["available_capabilities_missing_adapters"] == []
    assert audit["adapters_without_capabilities"] == []
    assert audit["direct_handoffs"]["relationship"] == "native_guide_relationship_handling"
