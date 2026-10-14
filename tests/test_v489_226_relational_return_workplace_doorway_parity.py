"""Regression tests for deterministic HRN workplace return doorways."""

import main


def test_verified_workplace_candidate_overrides_vector_pool_variation(monkeypatch):
    original = (
        "I keep returning to the agreed deadline because the project scope changed afterward. "
        "My colleague says I'm making too much of it. I want to understand what is happening between us."
    )
    verified = {
        "title": "🔥ARC I: The real problem isn't conflict. It's the conversations your system is not designed to hold.",
        "text": (
            "The Conflict & Trust Arc examines conflict and trust in workplace and team conversations. "
            "Project scope, deadlines, changed agreements, and shared responsibility can create disagreement "
            "when the work changes but expectations do not."
        ),
        "url": "https://geralddaquila.com/conflict-trust-arc/",
    }
    vector_candidate = {
        "title": "🧭 Conflict Moment Checklist",
        "text": "A general checklist for handling conflict moments in a relationship.",
        "url": "https://geralddaquila.com/2026/01/28/conflict-moment-checklist/",
    }
    monkeypatch.setattr(main, "_relational_return_verified_workplace_candidate", lambda query: verified)

    selected, outward = main._relational_return_apply_verified_workplace_candidate(
        original, original, vector_candidate, [vector_candidate]
    )

    assert selected is verified
    assert outward == [verified]


def test_verified_workplace_candidate_does_not_override_with_unqualified_page(monkeypatch):
    original = (
        "I keep returning to the agreed deadline because the project scope changed afterward. "
        "My colleague says I'm making too much of it. I want to understand what is happening between us."
    )
    unqualified = {
        "title": "🧭Orientation",
        "text": "A general entrance to the archive.",
        "url": "https://geralddaquila.com/orientation/",
    }
    vector_candidate = {
        "title": "Conflict Moment Checklist",
        "text": "A useful checklist for navigating conflict and shared expectations at work.",
        "url": "https://geralddaquila.com/conflict-moment-checklist/",
    }
    monkeypatch.setattr(main, "_relational_return_verified_workplace_candidate", lambda query: unqualified)

    selected, outward = main._relational_return_apply_verified_workplace_candidate(
        original, original, vector_candidate, [vector_candidate]
    )

    assert selected is vector_candidate
    assert outward == [vector_candidate]
