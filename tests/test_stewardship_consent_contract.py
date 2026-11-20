from pathlib import Path
import ast
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


def test_final_boundary_repairs_stewardship_only_answer_and_restores_doorway():
    payload = {"response": "Stewardship means taking care of something entrusted to you."}
    result = apply_stewardship_consent_relationship_boundary(
        "What is the relationship between stewardship and consent?", payload
    )
    assert result["processing"] == "final_visitor_boundary_stewardship_consent_relational_contract"
    assert has_stewardship_consent_relationship_explanation(result["response"])
    assert result["doorway_selection_status"] == "VERIFIED_RELEVANT_DESTINATION"
    assert result["doorway_url"] == canonical_doorway()["url"]


def test_final_boundary_preserves_a_complete_provider_answer():
    answer = recovery_response()
    payload = {"response": answer, "provider": "test-provider"}
    result = apply_stewardship_consent_relationship_boundary(
        "How do stewardship and consent relate?", payload
    )
    assert result["response"] == answer
    assert result["provider"] == "test-provider"
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


def test_query_family_selector_selects_the_stewardship_consent_doorway():
    root = Path(__file__).resolve().parents[1]
    source = (root / "main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_select_verified_doorway_conceptual_family"
    )
    namespace = {"re": re, "is_stewardship_consent_relationship_question":
                 is_stewardship_consent_relationship_question}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "<family>", "exec"), namespace)
    selector = namespace["_select_verified_doorway_conceptual_family"]
    assert selector("What is the relationship between stewardship and consent?") == (
        "stewardship_consent_relational_legitimacy"
    )
