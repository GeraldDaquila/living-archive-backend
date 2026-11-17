"""Regression tests for the formal-rules / informal-norms Guide contract."""

import main


QUERY = (
    "How should the Guide compare formal institutional rules with informal norms "
    "when explaining why an organization behaves as it does?"
)


def test_formal_rules_and_informal_norms_contract_sets_complete_answer_and_doorway(monkeypatch):
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda query: None)

    result = main._guide_finalize_visitor_payload(
        {"response": "provider placeholder", "recommendation": None},
        QUERY,
    )

    answer = result["response"]
    assert answer.startswith("An organization behaves according to more than its formal rules.")
    assert "Formal institutional rules are codified" in answer
    assert "Informal norms are socially maintained" in answer
    assert all(term in answer for term in (
        "reinforce formal rules",
        "circumvent them",
        "contradict them",
        "repeated consequences",
        "formally designed",
        "actually practiced",
    ))
    assert result["answer"] == answer
    assert result["recommendation"]["title"] == "Building Trust-Centered Organizations"
    assert result["recommendation"]["url"] == (
        "https://geralddaquila.com/2026/09/07/building-trust-centered-organizations/"
    )
    assert result["canonical_doorway"] == result["recommendation"]
    assert result["doorway_rationale"]
    assert result["processing"] == "final_visitor_boundary_formal_rules_informal_norms"


def test_formal_rules_and_informal_norms_contract_normalizes_case_and_whitespace(monkeypatch):
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda query: None)
    query = (
        "  HOW SHOULD THE GUIDE COMPARE FORMAL INSTITUTIONAL RULES WITH INFORMAL NORMS "
        "WHEN EXPLAINING WHY AN ORGANIZATION BEHAVES AS IT DOES?  "
    )

    result = main._guide_finalize_visitor_payload({"response": "placeholder"}, query)

    assert result["processing"] == "final_visitor_boundary_formal_rules_informal_norms"
    assert "interaction between" in result["response"]


def test_formal_rules_and_informal_norms_contract_does_not_capture_adjacent_questions(monkeypatch):
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda query: None)
    query = "How can an institution recognize that its formal structure and actual power structure differ?"

    result = main._guide_finalize_visitor_payload({"response": "provider answer"}, query)

    assert result["response"] == "provider answer"
    assert result.get("processing") != "final_visitor_boundary_formal_rules_informal_norms"
