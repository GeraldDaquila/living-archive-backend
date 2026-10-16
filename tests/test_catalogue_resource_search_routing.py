"""Routing boundary tests for native Catalogue resource search."""
import main


def test_explicit_material_search_routes_to_catalogue():
    assert main._is_catalogue_resource_search_query(
        "Where can I find material about institutional responsibility?"
    )
    assert main._is_catalogue_resource_search_query(
        "Find resources about governance and shared stewardship."
    )
    assert main._is_catalogue_resource_search_query(
        "Please recommend resources on stewardship."
    )


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
    assert query in payload["catalogue_url"] or "catalogue_query=" in payload["catalogue_url"]
    assert payload["response"] == ""
