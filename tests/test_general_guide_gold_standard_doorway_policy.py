"""Regression tests for the system-wide answer-then-doorway contract."""

import main


def test_blank_gold_standard_doorway_does_not_disable_default_relevant_doorway():
    # A frozen answer can intentionally omit its doorway without forbidding
    # an independently selected, verified canonical destination.
    standard = {
        "doorway_title": "",
        "doorway_url": "",
        "forbids_doorway": False,
    }

    candidate = {
        "title": "Foundational Stewardship Cases",
        "url": "https://geralddaquila.com/level-1-case-catalog/",
    }
    assert main._enforce_registered_gold_standard_doorway(candidate, standard) == candidate


def test_explicit_no_handoff_gold_standard_still_suppresses_doorway():
    standard = {
        "doorway_title": "",
        "doorway_url": "",
        "forbids_doorway": True,
        "doorway_omission_exception_reason": "An additional link would interrupt the immediate visitor response.",
    }

    candidate = {
        "title": "Foundational Stewardship Cases",
        "url": "https://geralddaquila.com/level-1-case-catalog/",
    }
    assert main._enforce_registered_gold_standard_doorway(candidate, standard) is None



def test_gold_standard_title_without_url_never_becomes_null_url_doorway():
    standard = {
        "doorway_title": "Leadership Beyond Control: The Rise of Coherence-Based Governance",
        "doorway_url": "",
        "forbids_doorway": False,
    }
    independently_verified = {
        "title": "A Canonical Systems Resource",
        "url": "https://geralddaquila.com/a-canonical-systems-resource/",
    }

    assert main._apply_registered_gold_standard_doorway(
        independently_verified, standard
    ) == independently_verified
    fallback = main._apply_registered_gold_standard_doorway(None, standard)
    assert fallback["title"] == "Sovereign Sensemaking Compass"
    assert fallback["url"] == "https://geralddaquila.com/the-sovereign-sensemaking-compass/"
    assert fallback["rationale"]


def test_complete_gold_standard_doorway_pair_can_override_verified_selection():
    standard = {
        "doorway_title": "Approved Canonical Resource",
        "doorway_url": "https://geralddaquila.com/approved-canonical-resource/",
        "forbids_doorway": False,
    }
    independently_verified = {
        "title": "Other Canonical Resource",
        "url": "https://geralddaquila.com/other-canonical-resource/",
    }

    assert main._apply_registered_gold_standard_doorway(
        independently_verified, standard
    ) == {
        "title": "Approved Canonical Resource",
        "url": "https://geralddaquila.com/approved-canonical-resource/",
    }


def test_gold_standard_invalid_url_cannot_override_verified_selection():
    standard = {
        "doorway_title": "Unverified Resource",
        "doorway_url": "https://example.org/unverified-resource/",
        "forbids_doorway": False,
    }
    independently_verified = {
        "title": "Relevant Archive Resource",
        "url": "https://geralddaquila.com/relevant-archive-resource/",
    }

    assert main._apply_registered_gold_standard_doorway(
        independently_verified, standard
    ) == independently_verified


def test_gold_standard_explicit_no_handoff_suppresses_every_doorway():
    standard = {
        "doorway_title": "",
        "doorway_url": "",
        "forbids_doorway": True,
        "doorway_omission_exception_reason": "A separate link would undermine the immediate visitor experience.",
    }
    independently_verified = {
        "title": "Relevant Archive Resource",
        "url": "https://geralddaquila.com/relevant-archive-resource/",
    }

    assert main._apply_registered_gold_standard_doorway(
        independently_verified, standard
    ) is None


def test_transformation_inquiry_gold_star_doorway_policy():
    """Gold-star calibration for coherent personal transformation doorways."""
    query = "How can a user distinguish genuine transformation from temporary emotional relief?"
    profile = {"risk": False, "action": "explanatory"}

    irrelevant = {
        "title": "Philippine Renewal Framework",
        "url": "https://geralddaquila.com/philippine-renewal-framework/",
        "text": "A framework for renewal of Philippine institutions, public systems, governance, and civic life.",
    }
    direct = {
        "title": "After the Awakening: A Gentle Map for the Road That Follows",
        "url": "https://geralddaquila.com/after-the-awakening/",
        "text": "A reflective guide to what follows an awakening: continuity, changed patterns, integration, and sustaining transformation over time.",
    }

    assert not main._eligible_outward_doc(query, irrelevant, profile)
    assert main._eligible_outward_doc(query, direct, profile)


def test_complete_gold_standard_doorway_preserves_registry_authored_rationale():
    standard = {
        "doorway_title": "Systems, Governance, and Organizational Design",
        "doorway_url": "https://geralddaquila.com/systems-structure/",
        "doorway_rationale": "This hub explains how structures and incentives shape durable system behavior.",
        "forbids_doorway": False,
    }
    result = main._apply_registered_gold_standard_doorway(None, standard)
    assert result == {
        "title": "Systems, Governance, and Organizational Design",
        "url": "https://geralddaquila.com/systems-structure/",
        "rationale": "This hub explains how structures and incentives shape durable system behavior.",
    }


def test_shared_restore_omits_doorway_when_no_relevant_candidate_exists(monkeypatch):
    monkeypatch.setattr(main, "_select_verified_doorway_conceptual_family", lambda query: "")
    monkeypatch.setattr(main, "_select_guide_node_fallback_doorway", lambda query: None)
    payload = {"response": "A complete answer."}

    result = main._guide_restore_verified_doorway(payload, "A general explanatory question?")

    assert result["recommendation"] is None
    assert result["canonical_doorway"] is None
    assert result["doorway_title"] is None
    assert result["doorway_url"] is None


def test_outermost_boundary_reapplies_doorway_after_all_inner_early_returns():
    from pathlib import Path

    source = (Path(main.__file__).resolve().parent / "main.py").read_text(encoding="utf-8")
    outer = source.index("safe_payload = _guide_finalize_visitor_payload(payload, query)")
    restore = source.index("safe_payload = _guide_restore_verified_doorway(safe_payload, query)", outer)
    provenance = source.index('safe_payload.setdefault("build_provenance"', outer)
    assert outer < restore < provenance


def test_reviewed_gold_star_exception_is_the_only_registry_based_suppression():
    assert main._gold_star_doorway_omission_is_justified({
        "forbids_doorway": True,
        "doorway_omission_exception_reason": "A link would interrupt the immediate safety response.",
    })
    assert not main._gold_star_doorway_omission_is_justified({
        "forbids_doorway": True,
        "doorway_omission_exception_reason": "",
    })
    assert not main._gold_star_doorway_omission_is_justified({
        "forbids_doorway": False,
        "doorway_omission_exception_reason": "No reason to omit.",
    })


def test_exact_water_gold_star_preserves_explicit_unapproved_doorway_omission():
    query = "What is the boiling point of water at sea level?"
    standard = main._resolve_exact_guide_gold_standard(query)
    assert standard is not None
    assert standard["forbids_doorway"] is True
    assert "no canonical url is inferred" in standard["doorway_omission_exception_reason"].casefold()
    assert main._gold_star_doorway_omission_is_justified(standard)

    default_doorway = main._gold_star_default_doorway()
    payload = {
        "response": standard["expected_response"],
        "recommendation": default_doorway,
        "canonical_doorway": default_doorway,
        "doorway_title": default_doorway["title"],
        "doorway_url": default_doorway["url"],
        "doorway_rationale": default_doorway["rationale"],
    }
    finalized = main._guide_finalize_visitor_payload(payload, query)
    restored = main._guide_restore_verified_doorway(finalized, query)

    assert finalized["recommendation"] is None
    assert finalized["canonical_doorway"] is None
    assert restored["recommendation"] is None
    assert restored["canonical_doorway"] is None
    assert restored["doorway_title"] is None
    assert restored["doorway_url"] is None
    assert restored["doorway_rationale"] is None


def test_unapproved_legacy_doorway_metadata_does_not_change_other_gold_star_fallbacks():
    # The no-doorway rule requires the explicit legacy status, a null expected
    # destination, and an explanatory note. An ordinary absent doorway is not
    # silently promoted into a global no-handoff policy.
    unrelated = main._resolve_exact_guide_gold_standard("What is governance, beyond administration?")
    assert unrelated is not None
    assert unrelated["forbids_doorway"] is False
