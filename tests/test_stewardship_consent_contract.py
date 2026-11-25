from pathlib import Path
import ast
import json
import re

from stewardship_consent_contract import (
    canonical_doorway,
    has_stewardship_consent_relationship_explanation,
    is_stewardship_consent_relationship_question,
    recovery_response,
    apply_stewardship_consent_relationship_boundary,
)


def test_recognizes_exact_question_and_close_relational_paraphrases():
    assert is_stewardship_consent_relationship_question(
        "What is the relationship between stewardship and consent?"
    )
    assert is_stewardship_consent_relationship_question(
        "How do stewardship and consent relate in practice?"
    )
    assert is_stewardship_consent_relationship_question(
        "What is the connection between consent and stewardship?"
    )
    assert not is_stewardship_consent_relationship_question("What is stewardship?")
    assert not is_stewardship_consent_relationship_question("What does consent mean?")


def test_recovery_explains_both_concepts_and_their_governing_relationship():
    answer = recovery_response()
    assert has_stewardship_consent_relationship_explanation(answer)
    folded = answer.casefold()
    for phrase in (
        "entrusted responsibility",
        "does not automatically confer authority",
        "consultation alone",
        "informed, voluntary, and specific",
        "refusal or withdrawal",
        "does not mean every ordinary act",
        "rather than allowing responsibility to turn into control",
    ):
        assert phrase in folded


def test_approved_registry_answer_satisfies_the_runtime_semantic_contract():
    root = Path(__file__).resolve().parents[1]
    registry = json.loads(
        (root / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8")
    )
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "gs-2026-11-20-stewardship-consent-relational-legitimacy"
    )
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert record["expected_response"] == recovery_response()
    assert has_stewardship_consent_relationship_explanation(record["expected_response"])


def test_validator_rejects_keyword_complete_but_relationally_wrong_answers():
    answer = (
        "Stewardship is entrusted responsibility to care, and consent is informed, voluntary, "
        "and specific. The steward's responsibility gives the steward authority over affected "
        "people. Consultation is consent when the intention is care. Affected people's agency "
        "matters, and refusal and withdrawal are possible. Ordinary care does not mean every "
        "action requires individual permission. These ideas are complementary and keep care "
        "accountable."
    )
    assert not has_stewardship_consent_relationship_explanation(answer)


def test_final_boundary_repairs_stewardship_only_answer_and_restores_doorway():
    payload = {
        "response": "Stewardship means taking care of something entrusted to you.",
        "provider": "weak-provider",
        "model": "weak-model",
        "evidence": [{"source": "unrelated"}],
    }
    result = apply_stewardship_consent_relationship_boundary(
        "What is the relationship between stewardship and consent?", payload
    )
    assert result["processing"] == "final_visitor_boundary_stewardship_consent_relational_contract"
    assert has_stewardship_consent_relationship_explanation(result["response"])
    assert result["doorway_selection_status"] == "VERIFIED_RELEVANT_DESTINATION"
    assert result["doorway_url"] == canonical_doorway()["url"]
    assert result["provider"] is None
    assert result["model"] is None
    assert result["evidence"] == []
    assert result["evidence_validation"]["status"] == "not_applicable"


def test_final_boundary_preserves_a_complete_provider_answer():
    answer = recovery_response()
    payload = {
        "response": answer,
        "provider": "test-provider",
        "answer_basis": {"kind": "retrieved_evidence", "label": "Evidence-backed"},
    }
    result = apply_stewardship_consent_relationship_boundary(
        "How do stewardship and consent relate?", payload
    )
    assert result["response"] == answer
    assert result["provider"] == "test-provider"
    assert result["answer_basis"]["kind"] == "retrieved_evidence"
    assert result["stewardship_consent_contract"]["answer_first_enforced"] is True


def test_runtime_wires_architectural_and_query_level_contracts():
    root = Path(__file__).resolve().parents[1]
    main_source = (root / "main.py").read_text(encoding="utf-8")
    guide_source = (root / "general_guide_composition.py").read_text(encoding="utf-8")
    assert "stewardship_consent_contract" in main_source
    assert "final_visitor_boundary_stewardship_consent_relational_contract" in main_source
    assert "is_stewardship_consent_relationship_question" in main_source
    assert "RELATIONAL SYNTHESIS — CONCEPT-PAIR QUESTIONS" in guide_source
    assert "responsibility does not automatically confer authority" in guide_source.casefold()


def test_actual_final_visitor_boundary_repairs_the_exact_query():
    root = Path(__file__).resolve().parents[1]
    source = (root / "main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_guide_finalize_visitor_payload"
    ][-1]
    namespace = {
        "re": re,
        "_sanitize_basic_inquiry_response": lambda value: value.strip(),
        "_guide_finalize_visitor_payload_inner": lambda payload, _query: payload,
        "APP_VERSION": "test",
        "_resolve_exact_guide_gold_standard": lambda _query: None,
        "_final_exact_gold_standard_authority": lambda _query: None,
        "_gold_star_doorway_omission_is_justified": lambda _standard: False,
        "_normalize_authoritative_recommendation": lambda value: value,
        # The production finalizer consults the request-local Gold Star ledger;
        # this AST-isolated test exercises the payload-trace fallback path.
        "_gold_star_ledger": type("LedgerStub", (), {
            "current_attempt_trace": lambda self: None,
            "current_request_context": lambda self: {"composition_attempt_count": 0},
        })(),
        "_emit_guide_outcome": lambda *_args, **_kwargs: None,
        "is_stewardship_consent_relationship_question": is_stewardship_consent_relationship_question,
        "_apply_stewardship_consent_relationship_boundary": apply_stewardship_consent_relationship_boundary,
    }
    exec(compile(ast.Module(body=[function], type_ignores=[]), "<finalizer>", "exec"), namespace)
    result = namespace["_guide_finalize_visitor_payload"](
        {
            "ok": True,
            "response": "Stewardship means taking care of something entrusted to you.",
            "provider": "weak-provider",
            "model": "weak-model",
            "evidence": [{"source": "unrelated"}],
        },
        "What is the relationship between stewardship and consent?",
    )
    assert result["processing"] == "final_visitor_boundary_stewardship_consent_relational_contract"
    assert has_stewardship_consent_relationship_explanation(result["response"])
    assert result["recommendation"]["url"] == canonical_doorway()["url"]
    assert result["provider"] is None
    assert result["model"] is None
    assert result["evidence"] == []


def test_query_family_selector_selects_the_stewardship_consent_doorway():
    root = Path(__file__).resolve().parents[1]
    source = (root / "main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    helper = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_guide_query_explicitly_forbids_handoff"
    )
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_select_verified_doorway_conceptual_family"
    )
    namespace = {"re": re, "is_stewardship_consent_relationship_question":
                 is_stewardship_consent_relationship_question}
    exec(compile(ast.Module(body=[helper, function], type_ignores=[]), "<family>", "exec"), namespace)
    selector = namespace["_select_verified_doorway_conceptual_family"]
    assert selector("What is the relationship between stewardship and consent?") == (
        "stewardship_consent_relational_legitimacy"
    )
