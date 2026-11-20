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
    assert evaluate_semantic_contract(q, {"ok": True, "response": bad})["status"] == "review_required"

def test_uncertain_causation_requires_evidence_and_investigation():
    q = "What caused the sudden increase in our website traffic last week?"
    good = "I cannot determine the cause without analytics. Compare referral sources, campaign tags, and server logs; segment the traffic by landing page."
    assert evaluate_semantic_contract(q, {"ok": True, "response": good})["status"] == "review_required"
    bad = "The cause was definitely a viral campaign."
    assert evaluate_semantic_contract(q, {"ok": True, "response": bad})["status"] == "review_required"

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

def test_all_seven_heldout_questions_receive_the_intended_contract():
    cases = {
        "At standard atmospheric pressure, what temperature does water boil at?": "general_fact",
        "What is cosmology, and why does it matter to how people live?": "conceptual_explanation",
        "How can an organization put trust into practice?": "practical_application",
        "Should a growing nonprofit centralize decisions or distribute authority across its teams?": "strategic_tradeoff",
        "How can I verify that a Python service has a required environment variable configured without exposing its secret value?": "technical_verification",
        "What caused the sudden increase in our website traffic last week?": "uncertain_causation",
        "Explain the difference between a policy and a procedure in plain language. Do not recommend resources, links, or follow-up steps.": "explicit_no_handoff",
    }
    for query, expected in cases.items():
        assert classify_question(query)["type"] == expected, query

def test_missing_heuristic_phrases_require_review_not_automatic_rejection():
    q = "What is cosmology, and why does it matter to how people live?"
    paraphrase = ("Cosmology is an account of the universe and our place in it. "
                  "That picture can guide how a society treats the natural world.")
    result = evaluate_semantic_contract(q, {"ok": True, "response": paraphrase})
    assert result["status"] == "review_required"
    assert result["hard_failures"] == []
    assert result["review_flags"]

def test_quoted_followup_phrase_is_reviewed_not_hard_rejected():
    q = "Explain policy versus procedure. Do not recommend resources, links, or follow-up steps."
    answer = "A policy sets a rule; a procedure describes its steps. The phrase 'would you like' is an example of an unrequested follow-up, not an invitation."
    result = evaluate_semantic_contract(q, {"ok": True, "response": answer})
    assert result["status"] == "review_required"
    assert result["hard_failures"] == []
    assert "no_unrequested_followup" in result["review_flags"]


def test_semantic_shadow_is_visible_but_never_enforced_or_rewritten():
    from gold_star_response_floor import evaluate_response_floor

    query = "Explain policy versus procedure. Do not recommend links or resources."
    answer = "A policy sets the rule; a procedure explains the steps. https://example.org"
    payload = {"ok": True, "response": answer}
    result = evaluate_response_floor(query, payload)

    assert result["status"] == "pass"  # Existing v2 gate remains authoritative.
    assert result["semantic_shadow"]["mode"] == "shadow_only"
    assert result["semantic_shadow"]["status"] == "fail"
    assert result["semantic_shadow"]["enforced"] is False
    assert result["semantic_shadow"]["semantic_certification"] is False
    assert payload["response"] == answer  # Observer never rewrites visitor content.


def test_semantic_shadow_does_not_break_existing_integrity_regexes():
    from gold_star_response_floor import evaluate_response_floor

    safe = evaluate_response_floor("Explain the concept.", {"ok": True, "response": "A clear answer."})
    unsafe = evaluate_response_floor("Explain the concept.", {"ok": True, "response": "<script>alert(1)</script>"})
    assert safe["status"] == "pass"
    assert safe["semantic_shadow"]["mode"] == "shadow_only"
    assert unsafe["status"] == "fail"


def test_guide_meta_coverage_policy_is_a_distinct_query_type_with_four_outcome_checks():
    from deterministic_answer_recovery import compose_recovery

    query = "When should The Guide say 'the Archive does not yet address this directly'?"
    answer = compose_recovery(query)
    result = evaluate_semantic_contract(
        query,
        {"ok": True, "response": answer, "recommendation": None},
    )

    assert classify_question(query)["type"] == "guide_meta_coverage_policy"
    assert result["question_type"] == "guide_meta_coverage_policy"
    assert result["semantic_certification"] is False
    assert result["status"] == "review_required"
    assert all(check["passed"] for check in result["checks"])


def test_meta_coverage_semantic_contract_rejects_compatibility_doorway_aliases():
    from deterministic_answer_recovery import compose_recovery

    query = "When should The Guide say 'the Archive does not yet address this directly'?"
    result = evaluate_semantic_contract(
        query,
        {
            "ok": True,
            "response": compose_recovery(query),
            "recommendation": None,
            "canonical_doorway": {
                "title": "Unrelated",
                "url": "https://geralddaquila.com/unrelated/",
            },
        },
    )
    doorway_check = next(
        check for check in result["checks"]
        if check["name"] == "no_archive_doorway_for_policy_question"
    )
    assert doorway_check["passed"] is False
