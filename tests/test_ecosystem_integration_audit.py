"""Contract tests for the non-secret ecosystem integration audit endpoint."""

import main
from main import ecosystem_integration_audit


def test_integration_audit_reports_runtime_registry_distinction():
    report = ecosystem_integration_audit()
    assert report["audit_contract"] == "ecosystem-integration-audit-v1"
    assert report["version"] == "v489.165"
    assert report["fingerprint"] == "USE-v489.165-guide-node-level-two-tuple-index"
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
