"""Terminal doorway suppression must override every earlier recommendation path."""

import main


def test_explicit_visitor_no_handoff_request_clears_all_public_doorway_aliases():
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
        # These are the exact compatibility aliases read by the live browser.
        "authoritative_doorway": {
            "title": "Living Glossary",
            "url": "https://geralddaquila.com/glossary/",
        },
        "canonical_recommendation": {
            "title": "Living Glossary",
            "url": "https://geralddaquila.com/glossary/",
        },
        "archive_doorway": {
            "title": "Living Glossary",
            "url": "https://geralddaquila.com/glossary/",
        },
        "doorway_decision": "omit",
        "doorway_omission_reason": (
            "No directly relevant canonical destination has been verified; "
            "do not substitute a generic fallback."
        ),
    }

    result = main._guide_enforce_terminal_doorway_policy(
        payload,
        "What is cosmology, and why does it matter to how people live? Please do not show a doorway or link.",
    )

    assert result["response"] == payload["response"]
    assert result["recommendation"] is None
    assert result.get("canonical_doorway") is None
    assert result["doorway_title"] is None
    assert result["doorway_url"] is None
    assert result["recommendation_canonical_primary"] is None
    assert result["authoritative_doorway"] is None
    assert result["canonical_recommendation"] is None
    assert result["archive_doorway"] is None
    assert "do not substitute a generic fallback" in result["doorway_omission_reason"]
    assert result["doorway_decision"] == "omit"


def test_unverified_upstream_recommendation_is_rejected_sitewide_when_no_source_supports_it():
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
    assert result.get("canonical_doorway") is None
    assert result["doorway_decision"] == "omit"
    assert result["doorway_omission_reason"]


def test_cosmology_lived_question_replaces_generic_glossary_with_direct_canonical_continuation():
    payload = {
        "response": "A complete explanation of cosmology and human life.",
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
    }

    result = main._guide_enforce_terminal_doorway_policy(
        payload,
        "What is cosmology, and why does it matter to how people live?",
    )

    assert result["recommendation"]["title"] == "The Hidden Assumptions That Quietly Shape Every Life"
    assert result["recommendation"]["url"] == "https://geralddaquila.com/2026/08/09/constitutional-ontology-hidden-maps/"
    assert result["doorway_decision"] == "selected"
    assert result["doorway_title"] == "The Hidden Assumptions That Quietly Shape Every Life"
    assert result["doorway_url"] == "https://geralddaquila.com/2026/08/09/constitutional-ontology-hidden-maps/"


def test_upstream_omission_note_does_not_block_sitewide_canonical_selection(monkeypatch):
    query = "What is cosmology, and why does it matter to how people live?"
    selected = {
        "title": "The Hidden Assumptions That Quietly Shape Every Life",
        "url": "https://geralddaquila.com/2026/08/09/constitutional-ontology-hidden-maps/",
        "rationale": (
            "This Cornerstone examines how inherited assumptions shape worldview, "
            "decisions, and everyday life."
        ),
    }
    payload = {
        "response": "A complete explanation.",
        "recommendation": None,
        "canonical_doorway": None,
        "doorway_omission_reason": (
            "An upstream recovery did not identify a direct destination."
        ),
    }

    def restore(safe, received_query):
        assert received_query == query
        return {
            **safe,
            "recommendation": selected,
            "canonical_doorway": selected,
            "doorway_title": selected["title"],
            "doorway_url": selected["url"],
            "doorway_rationale": selected["rationale"],
            "doorway_decision": "selected",
            "doorway_omission_reason": None,
        }

    monkeypatch.setattr(main, "_guide_restore_verified_doorway", restore)
    result = main._guide_enforce_terminal_doorway_policy(payload, query)

    assert result["recommendation"] == selected
    assert result["canonical_doorway"] == selected
    assert result["doorway_decision"] == "selected"
    assert result["doorway_omission_reason"] is None


def test_shared_doorway_restoration_emits_one_explicit_selection_or_omission(monkeypatch):
    query = "What is cosmology, and why does it matter to how people live?"
    selected = {
        "title": "The Hidden Assumptions That Quietly Shape Every Life",
        "url": "https://geralddaquila.com/2026/08/09/constitutional-ontology-hidden-maps/",
        "rationale": "Examines how inherited assumptions shape worldview and daily decisions.",
    }
    monkeypatch.setattr(main, "_select_verified_doorway_conceptual_family", lambda _q: None)
    monkeypatch.setattr(main, "_select_guide_node_fallback_doorway", lambda _q: selected)
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda _q: None)

    result = main._guide_restore_verified_doorway(
        {
            "response": "A complete explanation.",
            "recommendation": None,
            "doorway_omission_reason": "No destination was found upstream.",
        },
        query,
    )

    assert result["doorway_decision"] == "selected"
    assert result["recommendation"] == selected
    assert result["doorway_omission_reason"] is None

    monkeypatch.setattr(main, "_select_guide_node_fallback_doorway", lambda _q: None)
    omitted = main._guide_restore_verified_doorway(
        {"response": "A complete explanation.", "recommendation": None},
        "How does photosynthesis convert light into chemical energy?",
    )
    assert omitted["doorway_decision"] == "omit"
    assert omitted["recommendation"] is None
    assert omitted["doorway_omission_reason"]


def test_independent_canonical_selection_is_default_without_family_or_retrieval_context(monkeypatch):
    """A substantive answer gets a bounded Archive search even without a family match."""
    import deterministic_answer_recovery

    query = "How should a town balance individual choice with shared responsibilities?"
    selected = {
        "title": "A Verified Archive Continuation",
        "url": "https://geralddaquila.com/verified-continuation/",
        "rationale": "Explores the governance principles relevant to this question.",
    }
    calls = []

    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda _q: None)
    monkeypatch.setattr(main, "_select_verified_doorway_conceptual_family", lambda _q: None)
    monkeypatch.setattr(main, "_general_guide_authoritative_doorway",
                        lambda received_query, _payload: calls.append(received_query) or selected)
    monkeypatch.setattr(main, "_healthy_community_canonical_recommendation", lambda *_a: None)
    monkeypatch.setattr(main, "_trust_community_stewardship_canonical_recommendation", lambda *_a: None)
    monkeypatch.setattr(main, "_reciprocity_community_canonical_recommendation", lambda *_a: None)
    monkeypatch.setattr(main, "_select_guide_node_fallback_doorway", lambda _q: None)
    monkeypatch.setattr(deterministic_answer_recovery, "registered_recovery_recommendation", lambda _q: None)

    result = main._guide_restore_verified_doorway(
        {"response": "A complete substantive answer.", "processing": "unclassified_answer_route"},
        query,
    )

    assert calls == [query]
    assert result["doorway_decision"] == "selected"
    assert result["recommendation"] == selected
    assert result["doorway_selection_evaluated"] is True
    assert result["doorway_selection_source"] == "canonical_evidence_selector"


def test_reviewed_no_doorway_standard_remains_terminal_and_explicit():
    query = "A deliberately reviewed no-handoff calibration question."
    payload = {
        "response": "A complete answer.",
        "recommendation": {
            "title": "Generic Compass",
            "url": "https://geralddaquila.com/the-sovereign-sensemaking-compass/",
        },
    }
    # The exact standard is the only authority for this intentional exception.
    standard = {
        "forbids_doorway": True,
        "doorway_omission_exception_reason": "A handoff would interrupt this bounded answer.",
    }
    original = main._resolve_exact_guide_gold_standard
    try:
        main._resolve_exact_guide_gold_standard = lambda _q: standard
        result = main._guide_enforce_terminal_doorway_policy(payload, query)
    finally:
        main._resolve_exact_guide_gold_standard = original

    assert result["recommendation"] is None
    assert result["doorway_decision"] == "omit"
    assert "interrupt" in result["doorway_omission_reason"]

def test_json_sender_honors_exact_gold_star_no_doorway_authority():
    import asyncio
    import json

    query = "What does stewardship mean in the Living Archive?"
    standard = main._resolve_exact_guide_gold_standard(query)
    assert standard is not None
    assert standard["doorway_title"] == ""
    sent = []

    async def capture(message):
        sent.append(message)

    payload = {
        "query": query,
        "response": standard.get("expected_response") or "A complete answer.",
        "recommendation": {
            "title": standard.get("doorway_title"),
            "url": standard.get("doorway_url"),
            "rationale": standard.get("doorway_rationale"),
        },
    }
    asyncio.run(main._use_send_json(capture, payload))
    body = next(item["body"] for item in sent if item.get("type") == "http.response.body")
    result = json.loads(body.decode("utf-8"))

    assert result["doorway_decision"] == "omit"
    assert result["recommendation"] is None
    assert result.get("canonical_doorway") is None
    assert "no canonical doorway" in result["doorway_omission_reason"].casefold()

def test_json_sender_honors_explicit_no_handoff_instruction():
    import asyncio
    import json

    query = (
        "What is cosmology, and why does it matter to how people live? "
        "Please do not show a doorway or link."
    )
    sent = []

    async def capture(message):
        sent.append(message)

    payload = {
        "query": query,
        "response": (
            "Cosmology can refer to the scientific study of the universe or, "
            "in a broader philosophical sense, assumptions about reality."
        ),
        "recommendation": {
            "title": "The Hidden Assumptions That Quietly Shape Every Life",
            "url": "https://geralddaquila.com/2026/08/09/constitutional-ontology-hidden-maps/",
            "rationale": "A related philosophical continuation.",
        },
    }
    asyncio.run(main._use_send_json(capture, payload, status_code=503))
    body = next(item["body"] for item in sent if item.get("type") == "http.response.body")
    result = json.loads(body.decode("utf-8"))

    assert result["doorway_decision"] == "omit"
    assert result["recommendation"] is None
    assert result["canonical_doorway"] is None
    assert result["doorway_title"] is None
    assert result["doorway_url"] is None

def test_terminal_restoration_preserves_already_verified_server_selected_doorway(monkeypatch):
    query = "How can a community practice stewardship in everyday decisions?"
    selected = {
        "title": "Applied Stewardship Program",
        "url": "https://geralddaquila.com/applied-stewardship-program/",
        "rationale": "Its cases examine community stewardship through shared decisions and responsibilities.",
    }
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda _q: None)
    monkeypatch.setattr(
        main,
        "_general_guide_authoritative_doorway",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("terminal restoration must preserve the completed selection")
        ),
    )
    payload = {
        "response": "A complete practical answer.",
        "recommendation": selected,
        "canonical_doorway": selected,
        "doorway_selection_status": "VERIFIED_RELEVANT_DESTINATION",
        "doorway_selection_evaluated": True,
        "doorway_selection_source": "final_authoritative_recommendation_contract",
    }

    result = main._guide_restore_verified_doorway(payload, query)

    assert result["response"] == payload["response"]
    assert result["recommendation"] == selected
    assert result["canonical_doorway"] == selected
    assert result["doorway_title"] == selected["title"]
    assert result["doorway_url"] == selected["url"]
    assert result["doorway_decision"] == "selected"
    assert result["doorway_omission_reason"] is None

