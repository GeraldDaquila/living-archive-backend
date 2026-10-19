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


def test_explicit_definition_request_can_use_glossary():
    decision = resolve_route("Define reciprocity.")
    assert decision.route == "glossary"
    assert decision.mode == "lookup"


def test_practical_stewardship_question_is_not_glossary_routed():
    decision = resolve_route("What is stewardship in everyday community decisions?")
    assert decision.route == "guide"


def test_safety_precedence_over_new_bounded_routes():
    for query in (
        "Please run the Fractal Systems Diagnostic",
        "Show me the meaning of this glyph",
        "Define reciprocity.",
    ):
        decision = resolve_route(query, safety_active=True)
        assert decision.route == "safety"
        assert decision.mode == "safety"


def test_explicit_diagnostic_route_wins_over_generic_definition_language():
    decision = resolve_route("What is the Fractal Systems Diagnostic and can you run it?")
    assert decision.route == "fsd"
    assert decision.mode == "direct"


def test_open_ended_relationship_definition_stays_in_guide():
    decision = resolve_route("What is a healthy relationship?")
    assert decision.route == "guide"
    assert decision.mode == "direct"


def test_formation_surface_name_without_entry_intent_stays_in_guide():
    decision = resolve_route("What is the Stewardship Formation Navigator?")
    assert decision.route == "guide"
    assert decision.mode == "direct"


def test_unknown_mixed_question_remains_in_guide():
    decision = resolve_route("Compare public trust, stewardship, and institutional change.")
    assert decision.route == "guide"
    assert decision.mode == "direct"



def test_route_modes_stay_within_registry_contract():
    allowed_modes = {
        "guide": {"direct", "clarify"},
        "safety": {"safety"},
        "catalogue": {"lookup"},
        "formation": {"delegated_journey"},
        "fsd": {"direct"},
        "glyph": {"lookup"},
        "atlas": {"lookup"},
        "glossary": {"lookup"},
        "relationship": {"delegated_journey"},
        "navigator": {"lookup"},
        "systems_ph": {"lookup"},
        "case": {"lookup"},
    }
    queries = (
        "What makes a public institution trustworthy?",
        "Find case studies in the stewardship catalogue",
        "Open the Stewardship Formation Navigator",
        "Please run the Fractal Systems Diagnostic.",
        "Show me the meaning of this glyph.",
        "Show me the archive reference map.",
        "Define reciprocity.",
        "Help me understand the conflict in this relationship",
        "Where do I begin in the Living Archive?",
        "Open the Philippine Systems Lens.",
        "Find relevant case studies.",
    )
    for query in queries:
        decision = resolve_route(query)
        assert decision.route in allowed_modes
        assert decision.mode in allowed_modes[decision.route]


def test_glossary_accepts_explicit_what_does_term_mean_form():
    decision = resolve_route("What does reciprocity mean?")
    assert decision.route == "glossary"
    assert decision.mode == "lookup"


def test_glossary_exclusion_keeps_practical_stewardship_in_guide():
    decision = resolve_route("Define stewardship in everyday community decisions.")
    assert decision.route == "guide"


def test_safety_override_precedes_every_registered_specialist_route():
    queries = (
        "Find case studies in the stewardship catalogue",
        "Open the Stewardship Formation Navigator",
        "Please run the Fractal Systems Diagnostic.",
        "Show me the meaning of this glyph.",
        "Show me the archive reference map.",
        "Define reciprocity.",
        "Help me understand the conflict in this relationship",
    )
    for query in queries:
        decision = resolve_route(query, safety_active=True)
        assert decision.route == "safety"
        assert decision.mode == "safety"


def test_registry_snapshot_matches_registered_route_families():
    snapshot = registry_snapshot()
    assert snapshot["version"] == "v1"
    assert snapshot["rules"] == 10
    assert set(snapshot["routes"]) == {
        "guide", "safety", "catalogue", "formation", "fsd",
        "glyph", "atlas", "glossary", "relationship", "navigator", "systems_ph", "case",
    }
    assert snapshot["uses_llm_for_routing"] is False



def test_mentioning_formation_surface_is_not_enough_to_delegate():
    for query in (
        "Tell me about the Stewardship Formation Navigator.",
        "I saw the Formation Pathway mentioned in a document.",
        "What does the Stewardship Formation Navigator do?",
    ):
        decision = resolve_route(query)
        assert decision.route == "guide"
        assert decision.mode == "direct"


def test_formation_entry_language_still_delegates():
    for query in (
        "Open the Stewardship Formation Navigator.",
        "Please launch the Formation Pathway.",
        "Take me to the Stewardship Formation Navigator.",
    ):
        decision = resolve_route(query)
        assert decision.route == "formation"
        assert decision.mode == "delegated_journey"



def test_generic_maps_request_does_not_route_to_archive_atlas():
    for query in (
        "Show me maps of Manila.",
        "How do I get directions to the airport?",
        "Find a map of the Philippines.",
    ):
        decision = resolve_route(query)
        assert decision.route == "guide"
        assert decision.mode == "direct"


def test_archive_specific_map_request_routes_to_atlas():
    for query in (
        "Show me the archive reference map.",
        "Open the Archive Atlas.",
        "Find maps of the archive.",
    ):
        decision = resolve_route(query)
        assert decision.route == "atlas"
        assert decision.mode == "lookup"


def test_existential_meaning_of_life_question_stays_in_guide():
    for query in (
        "What is the meaning of life?",
        "What is the meaning of a good life?",
    ):
        decision = resolve_route(query)
        assert decision.route == "guide"
        assert decision.mode == "direct"


def test_specific_term_meaning_request_still_uses_glossary():
    decision = resolve_route("What is the meaning of reciprocity?")
    assert decision.route == "glossary"
    assert decision.mode == "lookup"


def test_explicit_archive_orientation_routes_to_navigator():
    decision = resolve_route("Where do I begin in the Living Archive?")
    assert decision.route == "navigator"
    assert decision.mode == "lookup"


def test_explicit_philippine_systems_lens_routes_to_specialist():
    decision = resolve_route("Open the Philippine Systems Lens.")
    assert decision.route == "systems_ph"
    assert decision.mode == "lookup"


def test_explicit_case_study_search_routes_to_case_navigator():
    decision = resolve_route("Find relevant case studies.")
    assert decision.route == "case"
    assert decision.mode == "lookup"


def test_case_study_mention_without_retrieval_intent_stays_in_guide():
    decision = resolve_route("Why are case studies useful for learning?")
    assert decision.route == "guide"
    assert decision.mode == "direct"
