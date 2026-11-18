"""Terminal doorway suppression must override every earlier recommendation path."""

import main


def test_explicit_recovery_omission_clears_generic_glossary_from_all_public_fields():
    payload = {
        "response": "A complete conceptual explanation.",
        "recommendation": {
            "title": "Living Glossary",
            "url": "https://geralddaquila.com/glossary/",
        },
        "canonical_doorway": {
            "title": "Living Glossary",
            "url": "https://geralddaquila.com/glossary/",
        },
        "doorway_title": "Living Glossary",
        "doorway_url": "https://geralddaquila.com/glossary/",
        "recommendation_canonical_primary": {
            "title": "Living Glossary",
            "url": "https://geralddaquila.com/glossary/",
        },
        "doorway_omission_reason": (
            "No directly relevant canonical cosmology resource has been verified; "
            "do not substitute a generic glossary link."
        ),
    }

    result = main._guide_enforce_terminal_doorway_policy(
        payload,
        "What is cosmology, and why does it matter to how people live?",
    )

    assert result["response"] == payload["response"]
    assert result["recommendation"] is None
    assert result["canonical_doorway"] is None
    assert result["doorway_title"] is None
    assert result["doorway_url"] is None
    assert result["recommendation_canonical_primary"] is None
    assert "do not substitute a generic glossary link" in result["doorway_omission_reason"]


def test_recovery_omission_is_a_sitewide_terminal_instruction_not_cosmology_only():
    payload = {
        "response": "A complete answer.",
        "recommendation": {
            "title": "Generic Compass",
            "url": "https://geralddaquila.com/the-sovereign-sensemaking-compass/",
        },
        "canonical_doorway": {
            "title": "Generic Compass",
            "url": "https://geralddaquila.com/the-sovereign-sensemaking-compass/",
        },
        "doorway_omission_reason": (
            "No verified destination materially advances this specific inquiry."
        ),
    }

    result = main._guide_enforce_terminal_doorway_policy(
        payload,
        "How does photosynthesis convert light into chemical energy?",
    )

    assert result["recommendation"] is None
    assert result["canonical_doorway"] is None
    assert result["doorway_omission_reason"] == payload["doorway_omission_reason"]


def test_cosmology_lived_question_cannot_keep_an_upstream_glossary_candidate():
    payload = {
        "response": "A complete explanation of cosmology and human life.",
        "recommendation": {
            "title": "The Living Glossary — Cosmology",
            "url": "https://geralddaquila.com/glossary/",
        },
        "doorway_title": "The Living Glossary — Cosmology",
        "doorway_url": "https://geralddaquila.com/glossary/",
    }

    result = main._guide_enforce_terminal_doorway_policy(
        payload,
        "What is cosmology, and why does it matter to how people live?",
    )

    assert result["recommendation"] is None
    assert result["doorway_title"] is None
    assert result["doorway_url"] is None
