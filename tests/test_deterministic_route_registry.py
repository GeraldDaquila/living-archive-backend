"""Contract tests for deterministic-first route resolution."""
from deterministic_route_registry import resolve_route, registry_snapshot


def test_explicit_catalogue_discovery_routes_without_model():
    decision = resolve_route("Find case studies in the stewardship catalogue")
    assert decision.route == "catalogue"
    assert decision.source == "deterministic-catalogue-task"


def test_catalogue_request_is_case_and_whitespace_insensitive():
    decision = resolve_route("  SEARCH   FOR archive resources  ")
    assert decision.route == "catalogue"


def test_explicit_formation_entry_routes_without_model():
    decision = resolve_route("Open the Stewardship Formation Navigator")
    assert decision.route == "formation"


def test_ordinary_stewardship_definition_is_not_misrouted_to_formation():
    decision = resolve_route("What is stewardship and why does it matter?")
    assert decision.route == "guide"


def test_explicit_relational_navigation_routes_to_relationship_specialist():
    decision = resolve_route("Help me understand the conflict in this relationship")
    assert decision.route == "relationship"


def test_practical_stewardship_question_stays_in_general_guide():
    decision = resolve_route(
        "How can a community practice stewardship in its everyday decisions and responsibilities?"
    )
    assert decision.route == "guide"
    assert decision.source == "deterministic-guide-default"


def test_safety_precedence_is_preserved_when_authoritative_boundary_is_active():
    decision = resolve_route("Find case studies in the catalogue", safety_active=True)
    assert decision.route == "safety"
    assert decision.confidence == 1.0


def test_unknown_question_defaults_to_guide_without_classification_call():
    decision = resolve_route("What makes a public institution trustworthy?")
    snapshot = registry_snapshot()
    assert decision.route == "guide"
    assert snapshot["uses_llm_for_routing"] is False
    assert snapshot["fallback"] == "guide"


def test_empty_query_requests_clarification():
    decision = resolve_route("  ")
    assert decision.route == "guide"
    assert decision.mode == "clarify"



def test_explicit_fsd_request_uses_diagnostic_route():
    decision = resolve_route("Please run the Fractal Systems Diagnostic.")
    assert decision.route == "fsd"
    assert decision.mode == "direct"


def test_explicit_glyph_lookup_uses_lookup_route():
    decision = resolve_route("Show me the meaning of this glyph.")
    assert decision.route == "glyph"
    assert decision.mode == "lookup"


def test_explicit_atlas_lookup_uses_lookup_route():
    decision = resolve_route("Show me the archive reference map.")
    assert decision.route == "atlas"
    assert decision.mode == "lookup"


def test_definition_request_can_use_glossary():
    decision = resolve_route("What is reciprocity?")
    assert decision.route == "glossary"
    assert decision.mode == "lookup"


def test_practical_stewardship_question_is_not_glossary_routed():
    decision = resolve_route("What is stewardship in everyday community decisions?")
    assert decision.route == "guide"


def test_safety_precedence_over_new_bounded_routes():
    for query in (
        "Please run the Fractal Systems Diagnostic",
        "Show me the meaning of this glyph",
        "What is reciprocity?",
    ):
        decision = resolve_route(query, safety_active=True)
        assert decision.route == "safety"
        assert decision.mode == "safety"
