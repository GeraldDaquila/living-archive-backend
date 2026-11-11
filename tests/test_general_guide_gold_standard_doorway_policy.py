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
    assert main._apply_registered_gold_standard_doorway(None, standard) is None


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
    }
    independently_verified = {
        "title": "Relevant Archive Resource",
        "url": "https://geralddaquila.com/relevant-archive-resource/",
    }

    assert main._apply_registered_gold_standard_doorway(
        independently_verified, standard
    ) is None


def test_general_personal_transformation_question_rejects_geographically_scoped_system_resource():
    query = "How can a user distinguish genuine transformation from temporary emotional relief?"
    profile = {"risk": False, "action": "explanatory"}
    decoy = {
        "title": "Philippine Renewal Framework",
        "url": "https://geralddaquila.com/philippine-renewal-framework/",
        "text": "A framework for renewal of Philippine institutions, public systems, governance, and civic life.",
    }
    assert not main._eligible_outward_doc(query, decoy, profile)


def test_general_personal_transformation_question_can_select_direct_transformation_resource():
    query = "How can a user distinguish genuine transformation from temporary emotional relief?"
    profile = {"risk": False, "action": "explanatory"}
    direct = {
        "title": "Transformation and Continuity",
        "url": "https://geralddaquila.com/transformation-and-continuity/",
        "text": "Transformation becomes visible over time through continuity, changed patterns, different choices, and a changed relationship to experience.",
    }
    assert main._eligible_outward_doc(query, direct, profile)


def test_transformation_inquiry_gold_star_doorway_policy():
    """Gold-star calibration: a personal transformation inquiry must not route
    to a geographically scoped institutional framework and must preserve a
    coherent, experiential continuation when an appropriate canonical resource
    is available."""
    query = "How can a user distinguish genuine transformation from temporary emotional relief?"
    profile = {"risk": False, "action": "explanatory"}

    irrelevant = {
        "title": "Philippine Renewal Framework",
        "url": "https://geralddaquila.com/philippine-renewal-framework/",
        "text": "A framework for renewal of Philippine institutions, public systems, governance, and civic life.",
    }
    coherent = {
        "title": "After the Awakening: A Gentle Map for the Road That Follows",
        "url": "https://geralddaquila.com/after-the-awakening/",
        "text": "A reflective guide to what follows an awakening: continuity, changed patterns, integration, and sustaining transformation over time.",
    }

    assert not main._eligible_outward_doc(query, irrelevant, profile)
    assert main._eligible_outward_doc(query, coherent, profile)
