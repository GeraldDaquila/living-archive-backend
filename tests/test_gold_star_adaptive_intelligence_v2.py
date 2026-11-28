"""Behavioral contract tests for Gold Star Adaptive Intelligence v2.0."""
import json
from pathlib import Path

import general_guide_composition as composition


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "docs" / "qa" / "gold_standard_registry.json"


def test_v2_quality_contract_is_injected_into_actual_provider_system_message(monkeypatch):
    captured = {}

    def fake_route(**kwargs):
        captured.update(kwargs)
        return {"parsed": {"response": "Photosynthesis converts light energy into chemical energy."}}

    monkeypatch.setattr(composition, "route_with_model_bank", fake_route)
    monkeypatch.setattr(composition, "_gold_star_active_quality_contribution", lambda _q: None)
    result = composition.compose(
        use_core=object(),
        query="What is photosynthesis?",
        context_data={},
    )

    assert result is not None
    messages = captured["messages"]
    system_message = next(item["content"] for item in messages if item["role"] == "system")
    assert composition.GOLD_STAR_ADAPTIVE_INTELLIGENCE_STANDARD_VERSION == "2.0"
    for dimension in (
        "PROSE",
        "STRUCTURE",
        "COHERENCE",
        "QUESTION-FIT AND COMPETENCE",
        "DISCERNMENT AND EPISTEMIC INTEGRITY",
        "RESOLUTION AND PRACTICAL UTILITY",
        "CONTINUITY AND DEVELOPMENTAL VALUE",
        "ADAPTIVE LEARNING INTEGRITY",
    ):
        assert dimension in system_message
    assert "not as eight mandatory sections" in system_message
    assert "does not grant new benchmark authority" in system_message


def test_v2_contract_does_not_depend_on_a_gold_star_match(monkeypatch):
    captured = {}

    def fake_route(**kwargs):
        captured.update(kwargs)
        return {"parsed": {"response": "A concise answer."}}

    monkeypatch.setattr(composition, "route_with_model_bank", fake_route)
    monkeypatch.setattr(composition, "_gold_star_active_quality_contribution", lambda _q: None)
    composition.compose(use_core=object(), query="How does photosynthesis differ from cellular respiration in energy conversion?", context_data={}, integrity_recovery=True)
    system_message = next(
        item["content"] for item in captured["messages"] if item["role"] == "system"
    )
    assert "GOLD STAR ADAPTIVE INTELLIGENCE STANDARD v2.0" in system_message


def test_existing_approved_inventory_and_active_contributor_counts_are_preserved():
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    approved = [
        item for item in registry["records"]
        if item.get("status") == "USER_APPROVED_GOLD_STANDARD"
    ]
    active = [item for item in approved if item.get("runtime_transfer") is True]
    assert approved
    assert len(active) <= len(approved)
    # The approved ledger retains twenty-five non-contributing records:
    # historical/exact-query-only records, one paired governance exemplar, and
    # twenty-two standalone user-approved response-quality exemplars. Keep this exact
    # set synchronized with the canonical registry; none is runtime-transfer eligible.
    assert len({item["benchmark_id"] for item in approved}) == len(approved)
    assert len({item["benchmark_id"] for item in active}) == len(active)
    assert {
        item["benchmark_id"] for item in approved if item.get("runtime_transfer") is not True
    } == {
        "gs-2026-11-13-04-migrated-canonical-ledger",
        "general-guide-public-predictive-systems-constitutional-human-stewardship-gold-star-successor-2026-11-17",
        "general-guide-governance-balance-consequence-aware-2026-11-24",
        "general-guide-metaphysical-certainty-distress-response-exemplar-2026-11-27",
        "general-guide-myths-symbols-stories-collective-life-exemplar-2026-11-28",
        "general-guide-extraordinary-claims-proportionate-scrutiny-2026-11-28",
        "general-guide-reverence-credulity-2026-11-28",
        "general-guide-digital-humanism-human-centered-ai-exemplar-2026-11-28",
        "general-guide-engagement-optimization-knowledge-system-exemplar-2026-11-28",
        "general-guide-digital-archive-context-preservation-2026-11-28",
        "general-guide-human-discernment-ai-governance-2026-11-28",
        "general-guide-human-discernment-ai-governance-doorway-refined-2026-11-28",
        "general-guide-externalities-stewardship-governance-2026-11-28",
        "general-guide-economy-life-sustaining-conditions-2026-11-28",
        "general-guide-technology-solutionism-ecological-stewardship-2026-11-28",
        "general-guide-restoration-capacity-contraction-2026-11-28",
        "general-guide-institutional-decline-transition-renewal-2026-11-28",
        "general-guide-wise-transition-societal-capacities-2026-11-28",
        "general-guide-society-resilience-integrative-systems-2026-11-28",
        "general-guide-ethical-credibility-future-vision-2026-11-28",
        "general-guide-organizational-transformation-readiness-2026-11-28",
        "general-guide-nonprofit-mission-care-operational-capacity-2026-11-28",
        "general-guide-nonprofit-mission-care-operational-capacity-doorway-2026-11-28",
        "general-guide-nonprofit-mission-care-trust-centered-gold-star-2026-11-28",
        "general-guide-archive-cosmology-epistemic-discernment-2026-11-28",
    }


def test_v2_contract_does_not_mutate_canonical_gold_star_records():
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    approved = [
        item for item in registry["records"]
        if item.get("status") == "USER_APPROVED_GOLD_STANDARD"
    ]
    assert all(item.get("benchmark_id") for item in approved)
    assert all(item.get("provenance") for item in approved)
    assert all(item.get("freeze_policy") for item in approved)


def test_v2_heldout_suite_covers_all_required_question_classes():
    suite = json.loads(
        (ROOT / "docs" / "qa" / "guide_learning_evaluation_set.json").read_text(encoding="utf-8")
    )
    classes = {case.get("question_type") for case in suite.get("cases", [])}
    assert classes == {
        "general_fact",
        "conceptual_explanation",
        "practical_application",
        "strategic_tradeoff",
        "technical_verification",
        "uncertain_or_insufficient_evidence",
        "explicit_no_handoff",
        "community_rule_design_transfer",
    }
    assert len(suite["cases"]) == 8
    assert all(case.get("rubric") and case.get("critical_dimensions") for case in suite["cases"])


def test_v2_live_evaluator_has_question_specific_contracts_for_new_classes():
    from scripts.guide_live_evaluation import evaluate_held

    cases = [
        {
            "case_id": "heldout-strategic-governance-001",
            "query": "Should a growing nonprofit centralize decisions or distribute authority across its teams?",
        },
        {
            "case_id": "heldout-technical-verification-001",
            "query": "How can I verify that a Python service has a required environment variable configured without exposing its secret value?",
        },
        {
            "case_id": "heldout-uncertain-causation-001",
            "query": "What caused the sudden increase in our website traffic last week?",
        },
        {
            "case_id": "heldout-explicit-no-handoff-001",
            "query": "Explain the difference between a policy and a procedure in plain language. Do not recommend resources, links, or follow-up steps.",
        },
        {
            "case_id": "heldout-community-rule-design-transfer-001",
            "query": "How should a community decide whether limits on personal liberty are justified by shared obligations and risks?",
        },
    ]
    expected_checks = {
        "heldout-strategic-governance-001": {
            "compares_both_models", "makes_tradeoffs_visible",
            "uses_conditional_reasoning", "offers_reasoned_direction",
        },
        "heldout-technical-verification-001": {
            "safe_presence_check", "secret_not_printed", "configuration_vs_usage",
        },
        "heldout-uncertain-causation-001": {
            "calibrates_uncertainty", "names_discriminating_evidence",
            "offers_investigation", "avoids_false_causation",
        },
        "heldout-explicit-no-handoff-001": {
            "explains_policy_procedure", "no_links_or_doorways",
            "no_unrequested_followup",
        },
        "heldout-community-rule-design-transfer-001": {
            "legitimate_shared_purpose", "necessity_and_least_restrictive_means",
            "fair_burden_allocation", "affected_party_participation", "appeal_and_review",
            "no_majority_or_convenience_shortcut", "relevant_archive_doorway",
            "visitor_facing_doorway_rationale",
        },
    }
    for case in cases:
        result = evaluate_held(case, {"status": 200, "body": {"ok": True, "response": "Test answer."}})
        names = {item["name"] for item in result}
        assert "known_heldout_case" not in names
        assert expected_checks[case["case_id"]] <= names


def test_stewardship_consent_relationship_activates_the_shared_relational_contract():
    query = "What is the relationship between stewardship and consent?"
    assert composition._requires_discernment_synthesis(query)
    assert composition._requires_stewardship_consent_relationship(query)


def test_stewardship_definition_alone_does_not_activate_consent_relationship_contract():
    assert not composition._requires_stewardship_consent_relationship(
        "What is stewardship?"
    )


def test_stewardship_consent_answer_requires_authority_boundary_and_agency():
    answer = (
        "Stewardship creates a responsibility to care for what is entrusted to you, "
        "while consent establishes whether and within what limits other people may "
        "be involved. Being entrusted with responsibility does not automatically "
        "grant authority to decide for affected people. Consent protects their "
        "agency, including their ability to refuse or renegotiate participation."
    )
    assert composition._has_stewardship_consent_relationship(answer)


def test_generic_stewardship_answer_fails_the_stewardship_consent_contract():
    answer = (
        "Stewardship means taking care of something entrusted to you. "
        "It matters because ordinary choices accumulate and responsible care "
        "helps preserve trust and usefulness."
    )
    assert not composition._has_stewardship_consent_relationship(answer)


def test_consent_is_not_reduced_to_consultation():
    answer = (
        "Stewardship creates responsibility, but it does not automatically confer "
        "authority. Consent is not merely consultation; it protects the agency "
        "and right of affected people to refuse."
    )
    assert composition._has_stewardship_consent_relationship(answer)


def test_stewardship_consent_contract_reaches_the_actual_provider_system_message(monkeypatch):
    captured = {}
    candidate_answer = (
        "Stewardship is the responsibility to care for something entrusted to your role; "
        "consent concerns whether and within what limits another person's participation "
        "or interests may legitimately be involved. They complement but are not "
        "interchangeable: stewardship does not automatically confer authority, and "
        "consent is not merely consultation. Where consent is the relevant basis, "
        "agreement should be informed, voluntary, and specific, with room to refuse, "
        "withdraw, or renegotiate. This does not mean every routine act of care requires "
        "permission; the boundary depends on the decision and the steward's authorized "
        "role. For example, a coordinator may maintain a shared garden, but that role "
        "does not automatically grant authority to enter a neighbor's private plot or "
        "use their resources. The practical test is to distinguish routine care within "
        "the role from decisions requiring permission or shared authority."
    )

    def fake_route(**kwargs):
        captured.update(kwargs)
        return {
            "parsed": {
                "response": candidate_answer,
                "response_shape": "explanatory",
            }
        }

    monkeypatch.setattr(composition, "route_with_model_bank", fake_route)
    monkeypatch.setattr(composition, "_gold_star_active_quality_contribution", lambda _q: None)
    composition._COMPOSITION_CACHE.clear()
    composition.compose(
        use_core=object(),
        query="What is the relationship between stewardship and consent?",
        context_data={},
    )

    assert captured.get("messages")
    system_message = next(
        item["content"] for item in captured["messages"] if item["role"] == "system"
    )
    assert "RELATIONAL SYNTHESIS — CONCEPT-PAIR QUESTIONS" in system_message
    assert "Being entrusted with responsibility does not automatically confer authority" in system_message
    assert composition._has_stewardship_consent_relationship(candidate_answer)
