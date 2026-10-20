"""Regression tests for deterministic HRN workplace return doorways."""

import json
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


def test_verified_workplace_candidate_fetches_real_canonical_page_contract(monkeypatch):
    original = (
        "I keep returning to the agreed deadline because the project scope changed afterward. "
        "My colleague says I'm making too much of it. I want to understand what is happening between us."
    )
    page = {
        "title": {"rendered": "🔥ARC I: The real problem isn't conflict. It's the conversations your system is not designed to hold."},
        "link": "https://geralddaquila.com/conflict-trust-arc/",
        "content": {
            "rendered": (
                "<h2>CONFLICT & TRUST BREAKDOWN</h2>"
                "<p>Most teams don't fail because of disagreement. They fail because disagreement is avoided.</p>"
                "<p>Conversations, meetings, and trust can break down when tension is not named.</p>"
            )
        },
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps(page).encode("utf-8")

    monkeypatch.setattr(main, "urlopen", lambda _request, timeout=3.0: FakeResponse())

    candidate = main._relational_return_verified_workplace_candidate(original)

    assert candidate is not None
    assert candidate["url"] == "https://geralddaquila.com/conflict-trust-arc/"
    assert main._relational_return_workplace_change_fit(original, candidate)



def test_credit_taking_in_a_lived_colleague_relationship_opens_hrn_boundary():
    query = (
        "I feel frustrated because my colleague keeps taking credit for work we did together. "
        "What might I be missing about the relationship?"
    )
    decision = main._relational_boundary_decision(query)
    assert decision["open"] is True
    assert decision["reason"] == "lived_relational_structure"
    assert decision["signals"]["first_person"] is True
    assert decision["signals"]["counterpart"] is True
    assert decision["signals"]["dynamic"] is True
    assert decision["signals"]["inquiry"] is True


def test_generic_question_about_credit_taking_does_not_open_hrn_boundary():
    query = "What are common patterns of taking credit in workplace relationships?"
    decision = main._relational_boundary_decision(query)
    assert decision["open"] is False
    assert decision["reason"] == "insufficient_converging_relational_evidence"
