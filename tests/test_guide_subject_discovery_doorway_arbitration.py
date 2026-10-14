"""Regression tests for subject discovery versus generic Archive navigation."""

import main


def _node(title, *, hints=(), asset_type="guide_node", node_id=None):
    return {
        "node_id": node_id or title.casefold().replace(" ", "-"),
        "title": title,
        "semantic_hints": list(hints),
        "asset_type": asset_type,
        "canonical_url": "https://geralddaquila.com/" + title.casefold().replace(" ", "-") + "/",
        "access_class": "public",
        "status": "active",
    }


def test_subject_discovery_does_not_resolve_to_libraries_from_broad_hints(monkeypatch):
    libraries = _node(
        "Libraries",
        hints=(
            "institutional responsibility",
            "governance materials",
            "find archive resources",
        ),
        asset_type="library_index",
    )
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [libraries])

    result = main._guide_node_specific_match(
        "Where can I find material about institutional responsibility?"
    )

    assert result is None


def test_explicit_request_for_libraries_can_still_select_libraries(monkeypatch):
    libraries = _node(
        "Libraries",
        hints=("institutional responsibility", "governance materials"),
        asset_type="library_index",
    )
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [libraries])

    result = main._guide_node_specific_match("Where can I find Libraries?")

    assert result is libraries


def test_subject_specific_registered_destination_beats_generic_library_hints(monkeypatch):
    libraries = _node(
        "Libraries",
        hints=("institutional responsibility", "governance materials"),
        asset_type="library_index",
    )
    institutional_stewardship = _node(
        "Institutional Stewardship",
        hints=("institutional responsibility", "institutional governance"),
        node_id="institutional-stewardship",
    )
    monkeypatch.setattr(
        main,
        "_guide_node_registry_snapshot",
        lambda: [libraries, institutional_stewardship],
    )

    result = main._guide_node_specific_match(
        "Where can I find material about institutional responsibility?"
    )

    assert result is institutional_stewardship


def test_generic_access_surface_does_not_match_by_asset_type_hints(monkeypatch):
    generic_index = _node(
        "Archive Reference Index",
        hints=("institutional responsibility", "stewardship frameworks"),
        asset_type="navigation_index",
    )
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [generic_index])

    result = main._guide_node_specific_match(
        "Where can I find material about institutional responsibility?"
    )

    assert result is None



def test_model_selected_unrelated_node_is_not_authorized_even_for_explicit_discovery(monkeypatch):
    libraries = _node(
        "Libraries",
        hints=("institutional responsibility", "find material"),
        asset_type="reference_territory",
    )
    unrelated = _node(
        "Living Stewardship",
        hints=("stewardship in practice", "applied stewardship"),
    )
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [libraries, unrelated])

    assert not main._guide_node_handoff_is_authorized(
        "Where can I find material about institutional responsibility?",
        "living-stewardship",
    )


def test_model_selected_node_must_match_registry_subject_destination(monkeypatch):
    libraries = _node(
        "Libraries",
        hints=("institutional responsibility", "find material"),
        asset_type="reference_territory",
    )
    leadership = _node(
        "Leadership Foundations",
        hints=("responsibility", "human systems", "governance and stewardship"),
    )
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [libraries, leadership])

    assert main._guide_node_handoff_is_authorized(
        "Where can I find material about leadership foundations?",
        "leadership-foundations",
    )
    assert not main._guide_node_handoff_is_authorized(
        "Where can I find material about leadership foundations?",
        "libraries",
    )
