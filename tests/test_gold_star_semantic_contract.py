from gold_star_semantic_contract import classify_question, evaluate_semantic_contract

def test_explicit_no_handoff_precedes_comparison():
    q = "Explain policy versus procedure. Do not recommend resources, links, or follow-up steps."
    assert classify_question(q)["type"] == "explicit_no_handoff"
    r = evaluate_semantic_contract(q, {"ok": True, "response": "A policy sets the rule; a procedure explains the steps."})
    assert r["status"] == "review_required" and all(c["passed"] for c in r["checks"])

def test_explicit_no_handoff_rejects_link():
    q = "Explain policy versus procedure. Do not recommend links or resources."
    r = evaluate_semantic_contract(q, {"ok": True, "response": "A policy sets the rule; a procedure explains the steps. https://example.org"})
    assert r["status"] == "fail"

def test_technical_verification_requires_presence_and_runtime_distinction():
    q = "How can I verify an environment variable is configured without exposing its secret value?"
    good = "Use os.getenv('TOKEN') is not None as a boolean presence check. This confirms configuration presence, not that the application reads it at runtime."
    assert evaluate_semantic_contract(q, {"ok": True, "response": good})["status"] == "review_required"
    bad = "Print(os.getenv('TOKEN')) to check it."
    assert evaluate_semantic_contract(q, {"ok": True, "response": bad})["status"] == "fail"

def test_uncertain_causation_requires_evidence_and_investigation():
    q = "What caused the sudden increase in our website traffic last week?"
    good = "I cannot determine the cause without analytics. Compare referral sources, campaign tags, and server logs; segment the traffic by landing page."
    assert evaluate_semantic_contract(q, {"ok": True, "response": good})["status"] == "review_required"
    bad = "The cause was definitely a viral campaign."
    assert evaluate_semantic_contract(q, {"ok": True, "response": bad})["status"] == "fail"

def test_unknown_and_fact_accuracy_never_auto_pass():
    assert evaluate_semantic_contract("Tell me something interesting", {"ok": True, "response": "Hello."})["status"] == "review_required"
    assert evaluate_semantic_contract("What is the boiling point of water?", {"ok": True, "response": "100°C."})["status"] == "review_required"

def test_contract_is_source_independent():
    q = "How can I verify an environment variable is configured without exposing its secret value?"
    a = "Use os.getenv('TOKEN') is not None as a presence check. This does not prove the application reads it at runtime."
    results = [evaluate_semantic_contract(q, {"ok": True, "response": a, "response_provenance": {"class": source}}) for source in ("llm", "deterministic_fallback")]
    assert results[0] == results[1]
def test_conceptual_explanation_is_not_misclassified_as_general_fact():
    q = "What is cosmology, and why does it matter to how people live?"
    assert classify_question(q)["type"] == "conceptual_explanation"
    good = ("Cosmology is the study of the universe as a whole. It matters because "
            "a picture of reality can shape people's values and choices. For example, "
            "a community's view of its place in the world can influence how it treats nature.")
    result = evaluate_semantic_contract(q, {"ok": True, "response": good})
    assert result["status"] == "review_required"
    assert all(check["passed"] for check in result["checks"])
