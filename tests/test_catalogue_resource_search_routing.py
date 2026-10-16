"""Routing boundary tests for native Catalogue resource search."""
from urllib.parse import quote

import main


def test_explicit_material_search_routes_to_catalogue():
    explicit_searches = (
        "Where can I find material about institutional responsibility?",
        "Find resources about governance and shared stewardship.",
        "Please recommend resources on stewardship.",
        "Can you help me find resources about institutional responsibility?",
        "Please search the archive for resources on stewardship.",
        "I'd like to browse works about stewardship.",
        "Show me works about institutional responsibility.",
        "What resources are available on stewardship?",
        "I'm looking for materials about shared governance.",
        "I want to explore the Catalogue for readings about stewardship.",
    )
    for query in explicit_searches:
        assert main._is_catalogue_resource_search_query(query), query


def test_explanatory_questions_stay_in_the_guide():
    assert not main._is_catalogue_resource_search_query(
        "What is stewardship and why does it matter now more than ever?"
    )
    assert not main._is_catalogue_resource_search_query(
        "Why is institutional responsibility important?"
    )
    assert not main._is_catalogue_resource_search_query(
        "What is stewardship? Where can I find material about it?"
    )


def test_catalogue_handoff_preserves_original_query_and_native_boundary():
    query = "Where can I find material about institutional responsibility?"
    payload = main._catalogue_handoff_payload(query, [])
    assert payload["intent"] == "CATALOGUE_HANDOFF"
    assert payload["handoff"] == "catalogue"
    assert payload["handoff_mode"] == "direct"
    assert payload["return_mode"] == "native_catalogue_search"
    assert payload["catalogue_query"] == query
    assert quote(query, safe="") in payload["catalogue_url"]
    assert payload["response"] == ""


def test_catalogue_is_available_as_native_handoff_not_adapter():
    audit = main.ecosystem_integration_audit()
    catalogue = next(
        item for item in audit["capability_registry"]
        if item["specialist_id"] == "catalogue"
    )

    assert catalogue["status"] == "available"
    assert audit["direct_handoffs"]["catalogue"] == "native_catalogue_search"
    assert "catalogue" not in audit["available_capabilities_missing_adapters"]
    assert audit["ok"] is True


def test_request_boundary_hands_explicit_resource_search_to_catalogue():
    from starlette.testclient import TestClient

    query = "Where can I find material about institutional responsibility?"
    with TestClient(main.app) as client:
        response = client.post("/api/query", json={"query": query})

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "CATALOGUE_HANDOFF"
    assert payload["handoff"] == "catalogue"
    assert payload["catalogue_query"] == query


def test_request_boundary_keeps_explanatory_question_in_guide(monkeypatch):
    from starlette.testclient import TestClient

    monkeypatch.setattr(
        main,
        "_basic_inquiry_response",
        lambda **kwargs: {"response": "A bounded Guide explanation."},
    )
    query = "What is stewardship and why does it matter now more than ever?"
    with TestClient(main.app) as client:
        response = client.post("/api/query", json={"query": query})

    assert response.status_code == 200
    payload = response.json()
    assert payload.get("intent") != "CATALOGUE_HANDOFF"
    assert payload.get("handoff") != "catalogue"
    assert "bounded Guide explanation" in str(payload.get("response") or payload)
