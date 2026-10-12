"""Contract tests for the non-secret ecosystem integration audit endpoint."""

import main
from main import ecosystem_integration_audit


def test_integration_audit_reports_runtime_registry_distinction():
    report = ecosystem_integration_audit()
    assert report["audit_contract"] == "ecosystem-integration-audit-v1"
    assert report["version"] == "v489.171"
    assert report["fingerprint"] == "USE-v489.171-hrn-compact-contract-recovery"
    assert report["fingerprint"]
    assert isinstance(report["capability_registry"], list)
    assert isinstance(report["runtime_adapters"], list)
    assert isinstance(report["direct_handoffs"], dict)


def test_integration_audit_does_not_misrepresent_catalogue_as_adapter():
    report = ecosystem_integration_audit()
    assert report["catalogue_mode"] == "direct_handoff_not_adapter"
    assert report["direct_handoffs"]["catalogue"] == "native_catalogue_search"
    assert report["direct_handoffs"]["systems_ph"] == "native_philippine_systems_landing"


def test_integration_audit_discloses_registry_adapter_gaps():
    report = ecosystem_integration_audit()
    assert "available_capabilities_missing_adapters" in report
    assert "adapters_without_capabilities" in report
    # A green registration report is not a substitute for visitor E2E.
    assert any("end-to-end" in item.lower() for item in report["limitations"])


def test_disagreement_does_not_invent_a_listening_topic_anchor():
    from main import _relational_return_topic_anchor

    anchor = _relational_return_topic_anchor(
        "One colleague holds to an agreed deadline while another points to changed scope.",
        "Clear communication of changes",
        "The original estimate did not include the added work.",
    )
    assert anchor == ""


def test_explicit_unheard_concern_still_adds_a_listening_topic_anchor():
    from main import _relational_return_topic_anchor

    anchor = _relational_return_topic_anchor(
        "I feel unheard when we disagree.",
        "Understand what happens in the conversation",
        "Listening and acknowledgment matter here.",
    )
    assert "Relational communication during disagreement" in anchor


def test_explicit_level_two_guide_node_returns_node_record_not_score(monkeypatch):
    node = {
        "node_id": "systems-stewardship",
        "title": "Systems Stewardship",
        "purpose": "A territory for systems stewardship and responsibility.",
        "semantic_hints": ["systems stewardship", "organizational patterns"],
        "discovery_level": 2,
    }
    monkeypatch.setattr(main, "_guide_node_registry_is_fresh", lambda: True)
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [node])

    activated = main._guide_node_semantic_activation(
        "Systems Stewardship",
        {},
        "guide",
    )

    assert activated == node


def test_heard_as_blame_does_not_add_listening_topic_anchor():
    from main import _relational_return_topic_anchor

    anchor = _relational_return_topic_anchor(
        "My partner and I keep having the same argument, even though we both want things to improve.",
        "Understand how raising an earlier hurt becomes a dispute about blame, without assuming either partner intends to hurt or dismiss the other.",
        "The argument changes direction when explaining an earlier hurt is heard as assigning blame.",
    )
    assert anchor == ""


def test_heard_as_blame_is_not_classified_as_a_listening_complaint():
    from main import _relational_communication_focus

    assert not _relational_communication_focus(
        "The argument changes direction when explaining an earlier hurt is heard as assigning blame."
    )
    assert _relational_communication_focus(
        "I feel unheard when my partner goes silent after an argument."
    )


def test_quoted_statements_do_not_merge_separate_topic_evidence():
    query = (
        "My partner and I keep having the same argument, even though we both say we want things to improve. "
        "Understand how raising an earlier hurt becomes a dispute about blame, without assuming either partner "
        "intends to hurt or dismiss the other. The argument changes direction when explaining an earlier hurt "
        "is heard as assigning blame."
    )
    self_sacrifice_article = {
        "title": "When Love Has Been Built on Your Self-Sacrifice",
        "text": (
            "You may think: “If I stop over-giving, they’ll feel hurt.” "
            "“If I set boundaries, I’ll seem selfish.” "
            "“If I change, I’ll damage the relationship.” "
            "But what you are really facing is this question: Can this relationship exist without my self-sacrifice holding it together? "
            "You are responsible for changing with honesty and care—not with blame, not with punishment, but with truth. "
            "There is a difference between attacking someone for the past and no longer participating in a pattern that harms you."
        ),
    }
    assert not main._relational_return_direct_topic_fit(query, self_sacrifice_article)
    assert not main._relational_return_earned_focus_fit(query, self_sacrifice_article)


def test_explicit_formation_entry_bypasses_ambiguous_model_route():
    query = "I want to enter stewardship formation and learn how to carry responsibility well."
    route = main._explicit_formation_entry_route(query)
    assert route is not None
    assert route["route"] == "formation"
    assert route["mode"] == "delegated_journey"
    assert route["source"] == "deterministic-explicit-formation-entry"
    assert route["round1_interpretation"]["presenting_situation"] == query


def test_formation_definition_question_is_not_forced_into_specialist_entry():
    route = main._explicit_formation_entry_route(
        "What is stewardship formation and why does it matter?"
    )
    assert route is None


def test_generated_observable_intention_language_does_not_create_discernment_focus():
    from main import _relational_return_topic_anchor

    anchor = _relational_return_topic_anchor(
        "My partner and I keep having the same argument, even though we both say we want things to improve.",
        "Understand how raising an earlier hurt becomes a dispute about blame, without assuming either partner intends to hurt or dismiss the other.",
        "This sequence is observable; each partner's intention remains unknown.",
    )
    assert "Relational discernment" not in anchor
    assert "Relational communication during disagreement" not in anchor


def test_explicit_perception_and_inference_question_still_gets_discernment_focus():
    from main import _relational_discernment_focus, _relational_return_topic_anchor

    query = "I can't tell whether what I'm sensing in this relationship is real or something I'm projecting."
    assert _relational_discernment_focus(query)
    anchor = _relational_return_topic_anchor(
        query,
        "Distinguish what I observed from what I inferred.",
        "What I infer may not match what happened.",
    )
    assert "Relational discernment" in anchor


def test_generic_communication_evidence_cannot_qualify_a_discernment_resource():
    from main import _relational_return_earned_focus_fit

    query = "I can't tell whether what I'm sensing in this relationship is real or something I'm projecting."
    broad_relationship_article = {
        "title": "When Love Has Been Built on Your Self-Sacrifice",
        "text": (
            "Many relationships form around roles we step into without realizing it. "
            "Listen without defensiveness. Acknowledge the imbalance and take responsibility."
        ),
    }
    assert not _relational_return_earned_focus_fit(query, broad_relationship_article)
