"""Regression contract: the Guide remains an Archive doorway when verified evidence exists."""
import main


def test_verified_retrieved_resource_is_recovered_when_strict_selection_returns_none(monkeypatch):
    query = "How should The Guide distinguish archive-grounded guidance from general external knowledge?"
    docs = [{
        "title": "Archive Grounding and Interpretation",
        "url": "https://geralddaquila.com/archive-grounding-and-interpretation/",
        "text": "The Archive distinguishes direct claims from synthesis and orientation, keeping each traceable to its evidence.",
    }]
    profile = {"action": "topical", "grief": False}

    monkeypatch.setattr(main, "_canonical_primary_from_docs", lambda docs, query, profile: docs[0])
    monkeypatch.setattr(main, "_select_guide_node_fallback_doorway", lambda query: None)

    doorway = main._verified_archive_doorway_fallback(query, docs, profile)

    assert doorway == {
        "title": "Archive Grounding and Interpretation",
        "url": "https://geralddaquila.com/archive-grounding-and-interpretation/",
    }


def test_no_verified_evidence_keeps_no_doorway(monkeypatch):
    monkeypatch.setattr(main, "_canonical_primary_from_docs", lambda docs, query, profile: None)
    monkeypatch.setattr(main, "_select_guide_node_fallback_doorway", lambda query: None)

    # Suppression is legitimate only when no verified canonical continuation exists.
    assert main._verified_archive_doorway_fallback(
        "A question with no verified Archive continuation", [], {"action": "topical"}
    ) is None


def test_systemwide_answer_recovery_does_not_clear_verified_navigation():
    from pathlib import Path

    source = Path("main.py").read_text(encoding="utf-8")
    start = source.index("# System-wide Gold Standard recovery:")
    end = source.index("if len(_systemwide_paragraphs)", start)
    recovery_boundary = source[start:end]

    assert "Preserve an already verified doorway" in recovery_boundary
    assert "authoritative_doorway = None" not in recovery_boundary


def test_reflective_balance_question_opens_bounded_canonical_doorway_lookup(monkeypatch):
    query = "How can hope remain disciplined rather than naïve?"
    approved = {
        "title": "Hope, Discernment, and Responsible Action",
        "url": "https://geralddaquila.com/hope-discernment-responsible-action/",
        "purpose": "A canonical resource on disciplined hope and discernment under uncertainty.",
        "semantic_hints": ["hope", "disciplined", "discernment", "uncertainty"],
    }
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [approved])

    assert main._select_verified_doorway_conceptual_family(query) == "reflective_conceptual_balance"
    assert main._select_guide_node_fallback_doorway(query) == {
        "title": approved["title"],
        "url": approved["url"],
        "rationale": approved["purpose"],
    }


def test_reflective_balance_question_does_not_invent_doorway_without_registry_evidence(monkeypatch):
    query = "How can hope remain disciplined rather than naïve?"
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [])

    assert main._select_verified_doorway_conceptual_family(query) == "reflective_conceptual_balance"
    assert main._select_guide_node_fallback_doorway(query) is None



def test_community_continuity_revision_recovers_its_verified_archive_doorway(monkeypatch):
    query = "How can communities preserve continuity while revising harmful inherited patterns?"
    assert main._is_conceptual_explanatory_request(query)
    assert main._select_verified_doorway_conceptual_family(query) == "community_continuity_revision"
    doorway = main._select_guide_node_fallback_doorway(query)
    assert doorway == {
        "title": "From Awakening to Stewardship",
        "url": "https://geralddaquila.com/from-awakening-to-stewardship/",
        "rationale": "This essay explores how personal development can mature into stewardship: taking responsibility for the relationships, institutions, and shared conditions that support human flourishing. It offers a wider perspective on community continuity by asking what people must build and sustain together, rather than prescribing how a particular inherited practice should be changed.",
    }

    monkeypatch.setattr(main, "_canonical_primary_from_docs", lambda docs, query, profile: None)
    recovered = main._verified_archive_doorway_fallback(query, [], {"action": "topical"})
    assert recovered == doorway



def test_community_continuity_recovery_is_registered_and_owns_its_verified_doorway():
    from deterministic_answer_recovery import (
        has_registered_recovery,
        registered_recovery_recommendation,
        compose_recovery,
    )

    query = "How can communities preserve continuity while revising harmful inherited patterns?"
    assert has_registered_recovery(query)
    assert registered_recovery_recommendation(query) == {
        "title": "From Awakening to Stewardship",
        "url": "https://geralddaquila.com/from-awakening-to-stewardship/",
        "rationale": "This essay explores how personal development can mature into stewardship: taking responsibility for the relationships, institutions, and shared conditions that support human flourishing. It offers a wider perspective on community continuity by asking what people must build and sustain together, rather than prescribing how a particular inherited practice should be changed.",
    }
    answer = compose_recovery(query)
    assert answer.startswith("Communities preserve continuity")
    assert len([p for p in answer.split("\n\n") if p.strip()]) == 3


def test_provider_exhaustion_path_returns_registered_answer_and_doorway_together():
    from deterministic_answer_recovery import registered_recovery_recommendation

    query = "How can communities preserve continuity while revising harmful inherited patterns?"
    result = main._basic_inquiry_provider_exhaustion_response(
        query,
        {},
        {"context_blocks": ""},
        recommendation_available=True,
    )
    expected_doorway = registered_recovery_recommendation(query)
    assert result["response"].startswith("Communities preserve continuity")
    assert len([p for p in result["response"].split("\n\n") if p.strip()]) == 3
    assert result["recommendation"] == expected_doorway
    assert result["doorway_title"] == expected_doorway["title"]
    assert result["doorway_url"] == expected_doorway["url"]

def test_ai_workforce_restructuring_selects_its_verified_canonical_doorway():
    query = (
        "A company wants to use AI to reduce staffing costs. How should The Guide "
        "analyze this through operations, governance, human development, ethics, and stewardship?"
    )
    assert main._select_verified_doorway_conceptual_family(query) == "ai_workforce_restructuring"
    assert main._select_guide_node_fallback_doorway(query) == {
        "title": "Agentic Systems and the End of Passive Labor",
        "url": "https://geralddaquila.com/2026/05/06/agentic-systems-and-the-end-of-passive-labor/",
        "rationale": (
            "This essay examines how AI changes work beyond task automation: it traces the shift "
            "across execution, coordination, and governance, and considers how human responsibility, "
            "oversight, and stewardship should evolve. It provides a relevant continuation for "
            "assessing workforce reductions as a redesign of work and accountability, not only a "
            "cost-saving exercise."
        ),
    }


def test_ai_workforce_doorway_is_not_selected_for_unrelated_ai_questions():
    assert main._select_verified_doorway_conceptual_family(
        "How can AI help me organize my personal reading notes?"
    ) is None


def test_shared_doorway_restoration_preserves_answer_and_syncs_frontend_contract():
    query = (
        "A company wants to use AI to reduce staffing costs. How should The Guide "
        "analyze this through operations, governance, human development, ethics, and stewardship?"
    )
    answer = "Provider-authored answer remains unchanged."
    restored = main._guide_restore_verified_doorway({"query": query, "response": answer}, query)
    expected = main._select_guide_node_fallback_doorway(query)

    assert restored["response"] == answer
    assert restored["recommendation"] == expected
    assert restored["canonical_doorway"] == expected
    assert restored["doorway_title"] == expected["title"]
    assert restored["doorway_url"] == expected["url"]
    assert restored["doorway_rationale"] == expected["rationale"]


def test_provider_and_deterministic_payloads_receive_same_final_doorway_contract():
    import asyncio
    import json
    from ai_workforce_restructuring_contract import (
        recovery_response,
        has_gold_star_coverage,
    )
    from general_guide_gold_standards import resolve_exact_gold_standard

    query = (
        "A company wants to use AI to reduce staffing costs. How should The Guide "
        "analyze this through operations, governance, human development, ethics, and stewardship?"
    )
    screenshot_answer = (
        "For a question like this, the first task is to make the decision visible. "
        "What outcome is the organisation trying to achieve, what responsibilities does it carry, "
        "and who will live with the consequences?\n\n"
        "From there, compare the real options rather than assuming that the proposed course is the only one. "
        "Look at what each option makes possible, what it may damage, who bears the costs, and what evidence "
        "would justify changing direction.\n\n"
        "The point is not to make the decision for the organisation, but to make the grounds for acting clearer. "
        "Choose deliberately, make the reasoning and limits visible, and remain accountable for what follows."
    )
    answer = recovery_response()
    assert not has_gold_star_coverage(screenshot_answer)
    assert has_gold_star_coverage(answer)

    standard = resolve_exact_gold_standard(query)
    assert standard["status"] == "USER_APPROVED_RELEASE_CANDIDATE"
    expected = {
        "title": standard["doorway_title"],
        "url": standard["doorway_url"],
        "rationale": standard["doorway_rationale"],
    }

    async def send_payload(provider):
        events = []

        async def send(event):
            events.append(event)

        payload = {
            "ok": True,
            "query": query,
            "response": screenshot_answer,
            "provider": provider,
            "recommendation": None,
            "canonical_doorway": None,
        }
        await main._use_send_json(send, payload)
        body = next(event["body"] for event in events if event["type"] == "http.response.body")
        return json.loads(body.decode("utf-8"))

    provider_payload = asyncio.run(send_payload("llm-provider"))
    deterministic_payload = asyncio.run(send_payload("deterministic-recovery"))

    for payload in (provider_payload, deterministic_payload):
        assert payload["response"] == standard["expected_response"]
        assert payload.get("answer_quality_contract") is None
        assert payload["recommendation"] == expected
        assert payload["canonical_doorway"] == expected
        assert payload["doorway_title"] == expected["title"]
        assert payload["doorway_url"] == expected["url"]
        assert payload["doorway_rationale"] == expected["rationale"]

def test_legacy_exact_standard_keeps_approved_answer_but_recovers_missing_verified_doorway(monkeypatch):
    import asyncio
    import json

    query = (
        "A company wants to use AI to reduce staffing costs. How should The Guide "
        "analyze this through operations, governance, human development, ethics, and stewardship?"
    )
    frozen_answer = "The exact approved historical answer remains unchanged."
    legacy_standard = {
        "expected_response": frozen_answer,
        "doorway_title": "",
        "doorway_url": "",
        "doorway_rationale": "",
        "forbids_doorway": False,
    }
    monkeypatch.setattr(
        main,
        "_resolve_exact_guide_gold_standard",
        lambda _query: legacy_standard,
    )

    async def send_payload():
        events = []

        async def send(event):
            events.append(event)

        payload = {"ok": True, "query": query, "response": "unapproved provider prose"}
        await main._use_send_json(send, payload)
        body = next(event["body"] for event in events if event["type"] == "http.response.body")
        return json.loads(body.decode("utf-8"))

    payload = asyncio.run(send_payload())
    expected = main._select_guide_node_fallback_doorway(query)
    assert payload["response"] == frozen_answer
    assert payload["recommendation"] == expected
    assert payload["canonical_doorway"] == expected
    assert payload["doorway_title"] == expected["title"]
    assert payload["doorway_url"] == expected["url"]
    assert payload["doorway_rationale"] == expected["rationale"]

def test_provider_and_deterministic_variants_share_workforce_gold_star_quality_floor():
    import asyncio
    import json
    from ai_workforce_restructuring_contract import recovery_response

    query = (
        "Our company is considering AI automation to lower employee headcount costs. "
        "What should we evaluate before making the change?"
    )
    assert main._resolve_exact_guide_gold_standard(query) is None
    assert main._select_verified_doorway_conceptual_family(query) == "ai_workforce_restructuring"
    weak_answer = (
        "For a question like this, the first task is to make the decision visible. "
        "What outcome is the organisation trying to achieve, what responsibilities does it carry, "
        "and who will live with the consequences?\n\n"
        "From there, compare the real options rather than assuming that the proposed course is the only one. "
        "Look at what each option makes possible, what it may damage, who bears the costs, and what evidence "
        "would justify changing direction.\n\n"
        "The point is not to make the decision for the organisation, but to make the grounds for acting clearer. "
        "Choose deliberately, make the reasoning and limits visible, and remain accountable for what follows."
    )

    async def send_payload(provider):
        events = []

        async def send(event):
            events.append(event)

        payload = {"ok": True, "query": query, "response": weak_answer, "provider": provider}
        await main._use_send_json(send, payload)
        body = next(event["body"] for event in events if event["type"] == "http.response.body")
        return json.loads(body.decode("utf-8"))

    expected_answer = recovery_response()
    expected_doorway = main._select_guide_node_fallback_doorway(query)
    for provider in ("llm-provider", "deterministic-recovery"):
        payload = asyncio.run(send_payload(provider))
        assert payload["response"] == expected_answer
        assert payload["answer_quality_contract"] == "ai_workforce_restructuring_gold_star_v1"
        assert payload["recommendation"] == expected_doorway
        assert payload["canonical_doorway"] == expected_doorway
        assert payload["doorway_rationale"] == expected_doorway["rationale"]

