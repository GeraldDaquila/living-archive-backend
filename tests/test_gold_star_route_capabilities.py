"""Regression tests for Guide-owned Gold Star route capability declarations."""
from gold_star_route_capabilities import (
    VERSION,
    registered_route_sources,
    route_capability,
    specialist_capability,
    registered_specialist_ids,
    validate_route_capability_registry,
)


OBSERVED_GUIDE_ROUTES = (
    "bounded_safety_conversation",
    "deterministic-formation-preparation-entry",
    "deterministic-systems-preparation-entry",
    "guide_basic_inquiry",
    "guide_basic_inquiry_recovery",
    "guide_broad_conceptual_boundary",
    "guide_direct_attribute_fail_closed",
    "guide_early_deterministic_boundary",
    "guide_explicit_home_navigation",
    "guide_final_visitor_boundary",
    "guide_hypothetical_safety_calibration",
    "guide_missing_context_guard",
    "guide_sitewide_safety_boundary",
    "registry_specific_destination",
)


def test_every_current_guide_route_has_a_bounded_capability_declaration():
    result = validate_route_capability_registry(OBSERVED_GUIDE_ROUTES)
    assert result["valid"] is True
    assert result["observed_unregistered"] == []
    assert result["registered_unobserved"] == []


def test_route_capability_declarations_are_versioned_and_never_semantic_certification():
    for route in OBSERVED_GUIDE_ROUTES:
        declaration = route_capability(route)
        assert declaration["version"] == VERSION
        assert declaration["declaration_status"] == "declared"
        assert declaration["scope"]
        assert declaration["semantic_competence_certified"] is False
        for field in (
            "supported_task_families",
            "unsupported_task_families",
            "evidence_modes",
            "abstention_modes",
        ):
            assert isinstance(declaration[field], list)


def test_unknown_route_is_not_granted_inferred_capability():
    declaration = route_capability("future_unregistered_route")
    assert declaration["declaration_status"] == "not_declared"
    assert declaration["supported_task_families"] == []
    assert declaration["route_class"] == "unclassified"
    assert declaration["semantic_competence_certified"] is False


def test_fail_closed_route_does_not_claim_a_supported_answer_task():
    declaration = route_capability("guide_direct_attribute_fail_closed")
    assert declaration["supported_task_families"] == []
    assert "fail_closed" in declaration["abstention_modes"]


def test_specialist_entry_is_bounded_and_guide_owned():
    declaration = route_capability("deterministic-formation-preparation-entry")
    assert declaration["route_class"] == "specialist_handoff"
    assert declaration["supported_task_families"] == ["stewardship_formation_orientation"]
    assert "specialist_unavailable" in declaration["abstention_modes"]
    assert "Guide retains final visitor-response authority" in declaration["scope"]



def test_systems_specialist_entry_is_bounded_and_guide_owned():
    declaration = route_capability("deterministic-systems-preparation-entry")
    assert declaration["route_class"] == "specialist_handoff"
    assert declaration["supported_task_families"] == ["bounded_philippine_systems_orientation"]
    assert "specialist_unavailable" in declaration["abstention_modes"]
    assert "Guide retains final visitor-response authority" in declaration["scope"]



def test_registered_specialist_capabilities_are_explicit_and_bounded():
    expected = {"relationship", "formation", "catalogue", "systems_ph", "safety"}
    assert set(registered_specialist_ids()) == expected
    for specialist_id in expected:
        declaration = specialist_capability(specialist_id)
        assert declaration["declaration_status"] == "declared"
        assert declaration["scope"]
        assert declaration["semantic_competence_certified"] is False
        for field in (
            "supported_task_families",
            "unsupported_task_families",
            "evidence_modes",
            "abstention_modes",
        ):
            assert isinstance(declaration[field], list)


def test_specialist_capability_unknown_identity_remains_unresolved():
    declaration = specialist_capability("future_specialist")
    assert declaration["declaration_status"] == "not_declared"
    assert declaration["supported_task_families"] == []
    assert declaration["semantic_competence_certified"] is False



def test_route_registry_stays_reconciled_with_main_runtime_route_sources():
    import re
    from pathlib import Path

    source = Path(__file__).resolve().parents[1].joinpath("main.py").read_text(encoding="utf-8")
    observed = set(re.findall(r"""["']route_source["']\s*:\s*["']([^"']+)["']""", source))
    assert observed == set(registered_route_sources())
