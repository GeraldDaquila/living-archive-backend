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


def test_glyph_meaning_question_is_not_captured_by_generic_glossary():
    decision = resolve_route("What does this glyph mean?")
    assert decision.route == "glyph"
    assert decision.mode == "lookup"


def test_explicit_catalogue_wins_when_case_study_is_also_requested():
    decision = resolve_route("Find case studies in the stewardship catalogue")
    assert decision.route == "catalogue"
    assert decision.mode == "lookup"


def test_case_study_search_does_not_require_catalogue_word():
    decision = resolve_route("Search for relevant case studies")
    assert decision.route == "case"
    assert decision.mode == "lookup"


def test_systems_lens_mention_without_task_intent_stays_in_guide():
    for query in (
        "What is the Philippine Systems Lens?",
        "I read about the Philippine Systems Lens.",
    ):
        decision = resolve_route(query)
        assert decision.route == "guide"
        assert decision.mode == "direct"


def test_systems_lens_explicit_invocation_routes_to_specialist():
    for query in (
        "Open the Philippine Systems Lens.",
        "Use the Philippine Systems Lens to examine this issue.",
        "Apply the Philippine Systems Lens to this policy question.",
    ):
        decision = resolve_route(query)
        assert decision.route == "systems_ph"
        assert decision.mode == "lookup"


def test_negated_systems_lens_invocation_stays_in_guide():
    for query in (
        "Do not open the Philippine Systems Lens.",
        "Don't apply the Philippine Systems Lens to this question.",
        "Never use the Philippine Systems Lens here.",
    ):
        decision = resolve_route(query)
        assert decision.route == "guide"
        assert decision.mode == "direct"


def test_negated_specialist_tasks_default_to_guide_across_route_families():
    for query in (
        "Do not find case studies.",
        "Don't search for archive resources.",
        "Never open the Stewardship Formation Navigator.",
        "Please do not run the Fractal Systems Diagnostic.",
        "Don't show me the archive reference map.",
        "Never define reciprocity for me.",
    ):
        decision = resolve_route(query)
        assert decision.route == "guide"
        assert decision.mode == "direct"
        assert decision.source == "deterministic-negated-task-guard"


def test_authoritative_safety_precedes_negated_task_guard():
    decision = resolve_route("Do not show me resources; I feel unsafe right now.", safety_active=True)
    assert decision.route == "safety"
    assert decision.mode == "safety"
    assert decision.source == "deterministic-safety-precedence"


def test_production_lived_projection_fixture_routes_to_relationship_specialist():
    query = (
        "I can't tell whether what I'm sensing in a relationship is real "
        "or something I'm projecting."
    )
    decision = resolve_route(query)
    assert decision.route == "relationship"
    assert decision.mode == "delegated_journey"
    assert decision.source == "deterministic-lived-relational-projection"


def test_bounded_archive_projection_article_search_stays_outside_relationship_route():
    query = (
        "Can you find an article in the Living Archive about projection in relationships?"
    )
    decision = resolve_route(query)
    assert decision.route == "catalogue"
    assert decision.mode == "lookup"


def test_projection_topic_without_first_person_uncertainty_stays_in_guide():
    for query in (
        "What is projection in relationships?",
        "Projection can affect how people interpret conflict.",
        "I read about projection in relationships.",
    ):
        decision = resolve_route(query)
        assert decision.route == "guide"
        assert decision.mode == "direct"


def test_production_catalogue_resource_search_fixtures_route_to_catalogue():
    # Mirrors the positive cases in tests/test_catalogue_resource_search_routing.py.
    for query in (
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
    ):
        decision = resolve_route(query)
        assert decision.route == "catalogue", query
        assert decision.mode == "lookup", query
        assert decision.source == "deterministic-catalogue-resource-search", query


def test_explanatory_questions_and_explanatory_first_mixed_queries_stay_in_guide():
    for query in (
        "What is stewardship and why does it matter now more than ever?",
        "Why is institutional responsibility important?",
        "What is stewardship? Where can I find material about it?",
    ):
        decision = resolve_route(query)
        assert decision.route == "guide", query
        assert decision.mode == "direct", query


def test_production_workplace_return_fixture_routes_relational_but_does_not_claim_history_parity():
    # Source: tests/test_v489_226_relational_return_workplace_doorway_parity.py.
    # This is a real single-turn production regression fixture, not a substitute
    # for multi-turn history/context parity testing.
    query = (
        "I keep returning to the agreed deadline because the project scope changed afterward. "
        "My colleague says I'm making too much of it. I want to understand what is happening between us."
    )
    decision = resolve_route(query)
    assert decision.route == "relationship"
    assert decision.mode == "delegated_journey"
    assert decision.source == "deterministic-relational-intent"



def test_collision_precedence_keeps_specific_task_over_generic_language():
    cases = (
        (
            "What is the Fractal Systems Diagnostic and can you run it?",
            "fsd",
            "direct",
        ),
        (
            "What does this glyph mean?",
            "glyph",
            "lookup",
        ),
        (
            "Find case studies in the stewardship catalogue",
            "catalogue",
            "lookup",
        ),
    )
    for query, expected_route, expected_mode in cases:
        decision = resolve_route(query)
        assert (decision.route, decision.mode) == (expected_route, expected_mode), query


def test_coordinated_negation_does_not_activate_any_negated_specialist_task():
    decision = resolve_route(
        "Please do not open the Philippine Systems Lens or find case studies."
    )
    assert decision.route == "guide"
    assert decision.mode == "direct"
    assert decision.source == "deterministic-negated-task-guard"


def test_contrastive_affirmative_task_survives_separate_negated_action():
    decision = resolve_route(
        "Do not open the Philippine Systems Lens, but find case studies."
    )
    assert decision.route == "case"
    assert decision.mode == "lookup"
    assert decision.source == "deterministic-case-study-lookup"
