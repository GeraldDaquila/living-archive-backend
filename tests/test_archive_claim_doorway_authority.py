"""Regression: provenance recovery cannot rerank visitor navigation."""

import main


def test_archive_claim_boundary_rejects_unrelated_upstream_doorway(monkeypatch):
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda q: None)
    query = "How does the Archive distinguish tools from the purposes they serve?"
    unrelated = {
        "title": "Why the AI Era Is Ultimately a Human Identity Crisis",
        "url": "https://geralddaquila.com/example/ai-identity-crisis/",
    }
    monkeypatch.setattr(main, "_guide_node_specific_match", lambda q: None)

    result = main._guide_finalize_visitor_payload(
        {"response": "placeholder", "recommendation": unrelated},
        query,
    )

    assert result["recommendation"] is None


def test_archive_claim_boundary_accepts_matching_registered_node(monkeypatch):
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda q: None)
    query = "How does the Archive distinguish tools from the purposes they serve?"
    canonical = {
        "title": "USE: The Protection Layer",
        "url": "https://geralddaquila.com/use-the-protection-layer/",
    }
    monkeypatch.setattr(main, "_guide_node_specific_match", lambda q: dict(canonical))

    result = main._guide_finalize_visitor_payload(
        {"response": "placeholder", "recommendation": dict(canonical)},
        query,
    )

    assert result["recommendation"] == canonical


def test_sender_cannot_repopulate_provenance_doorway_after_fail_closed(monkeypatch):
    query = "How does the Archive distinguish tools from the purposes they serve?"
    payload = {
        "query": query,
        "response": "placeholder",
        "recommendation": None,
        "processing": "final_visitor_boundary_archive_claim_provenance",
    }
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda q: None)

    sent = []
    async def capture(message):
        sent.append(message)

    import asyncio, json
    asyncio.run(main._use_send_json(capture, payload))
    body = json.loads(sent[-1]["body"].decode("utf-8"))
    assert body["recommendation"] is None


def test_archive_claim_boundary_clears_stale_canonical_doorway(monkeypatch):
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda q: None)
    query = "How does the Archive distinguish tools from the purposes they serve?"
    stale = {
        "title": "Why the AI Era Is Ultimately a Human Identity Crisis",
        "url": "https://geralddaquila.com/2026/09/14/why-the-ai-era-is-ultimately-a-human-identity-crisis/",
    }
    monkeypatch.setattr(main, "_guide_node_specific_match", lambda q: None)
    result = main._guide_finalize_visitor_payload(
        {"response": "placeholder", "recommendation": stale, "canonical_doorway": stale},
        query,
    )
    assert result["recommendation"] is None
    assert result["canonical_doorway"] is None


def test_public_commons_governance_question_selects_knowledge_sensemaking_doorway():
    query = (
        "What does the Archive's claim to be a public commons require in how the "
        "Guide handles access, attribution, disagreement, and stewardship?"
    )
    family = main._select_verified_doorway_conceptual_family(query)
    assert family == "public_commons_stewardship"

    result = main._guide_restore_verified_doorway({"response": "answer"}, query)
    assert result["recommendation"] == {
        "title": "Knowledge Stewardship in the AI Era: From Information to Wisdom",
        "url": "https://geralddaquila.com/2026/09/14/knowledge-stewardship-in-the-ai-era-from-information-to-wisdom/",
        "rationale": (
            "This Archive essay includes a section on knowledge as a commons and explains why shared knowledge depends on responsible preservation, interpretation, transparency, accountability, and thoughtful participation. It is a direct continuation into the stewardship of the knowledge conditions the Guide must help preserve."
        ),
    }
    assert result["doorway_title"] == result["recommendation"]["title"]
    assert result["doorway_url"] == result["recommendation"]["url"]


def test_public_commons_doorway_is_not_applied_to_unrelated_archive_claim():
    query = "What is the Archive's publication date?"
    assert main._select_verified_doorway_conceptual_family(query) != "archive_guidance_provenance"


def test_public_commons_gold_star_contract_is_enforced_for_provider_and_deterministic_payloads(monkeypatch):
    query = (
        "What does the Archive's claim to be a public commons require in how the "
        "Guide handles access, attribution, disagreement, and stewardship?"
    )
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda q: None)
    provider_payload = {"response": "provider draft without a doorway", "route_source": "provider"}
    deterministic_payload = {"response": "deterministic draft without a doorway", "route_source": "deterministic"}

    expected_doorway = {
        "title": "Knowledge Stewardship in the AI Era: From Information to Wisdom",
        "url": "https://geralddaquila.com/2026/09/14/knowledge-stewardship-in-the-ai-era-from-information-to-wisdom/",
        "rationale": (
            "This Archive essay includes a section on knowledge as a commons and explains why shared knowledge depends on responsible preservation, interpretation, transparency, accountability, and thoughtful participation. It is a direct continuation into the stewardship of the knowledge conditions the Guide must help preserve."
        ),
    }
    provider_result = main._guide_finalize_visitor_payload(provider_payload, query)
    deterministic_result = main._guide_finalize_visitor_payload(deterministic_payload, query)

    for result in (provider_result, deterministic_result):
        assert "not every resource has the same access status" in result["response"]
        assert "credit authorship" in result["response"]
        assert "quietly blending them into a consensus" in result["response"]
        assert result["recommendation"] == expected_doorway
        assert result["canonical_doorway"] == expected_doorway
        assert result["doorway_title"] == expected_doorway["title"]
        assert result["doorway_url"] == expected_doorway["url"]
        assert result["doorway_rationale"] == expected_doorway["rationale"]
        assert result["processing"] == "final_visitor_boundary_public_commons_stewardship"


def test_public_commons_gold_star_does_not_capture_unrelated_archive_questions(monkeypatch):
    query = "What is the Archive's publication date?"
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda q: None)
    payload = {"response": "ordinary answer", "recommendation": None}
    result = main._guide_finalize_visitor_payload(payload, query)
    assert result["response"] == "ordinary answer"
    assert result.get("processing") != "final_visitor_boundary_public_commons_stewardship"


def test_archive_examples_without_direct_answer_use_evidence_limits_contract_for_both_routes(monkeypatch):
    query = (
        "The archive offers two suggestive examples but no direct answer to a visitor's claim. "
        "How should the Guide express what is known and what remains open?"
    )
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda q: None)
    generic_decision_answer = (
        "Start by defining the outcome the change must achieve, the responsibilities that cannot "
        "be lost, and the people who will live with its consequences."
    )
    irrelevant_glossary = {
        "title": "Living Glossary",
        "url": "https://geralddaquila.com/living-glossary/",
    }
    payloads = (
        {"response": generic_decision_answer, "recommendation": dict(irrelevant_glossary), "route_source": "provider"},
        {"response": generic_decision_answer, "recommendation": dict(irrelevant_glossary), "route_source": "deterministic"},
    )

    assert main._is_archive_examples_evidence_limits_inquiry(query) is True
    results = [
        main._guide_finalize_visitor_payload(payload, query)
        for payload in payloads
    ]

    expected_doorway = {
        "title": "The Living Archive Navigator: Volume III – Knowledge & Sensemaking",
        "url": "https://geralddaquila.com/the-living-archive-navigator-volume-iii",
        "rationale": (
            "Continue into the Archive's Knowledge & Sensemaking pathway to examine how sources, "
            "evidence, interpretation, and unresolved questions relate."
        ),
    }
    for result in results:
        assert "The two examples establish what those particular sources actually say" in result["response"]
        assert "What remains open is whether the examples are representative" in result["response"]
        assert "Illustration is useful, but it is not proof." in result["response"]
        assert generic_decision_answer not in result["response"]
        assert result["recommendation"] == expected_doorway
        assert result["canonical_doorway"] == expected_doorway
        assert result["doorway_title"] == expected_doorway["title"]
        assert result["doorway_url"] == expected_doorway["url"]
        assert result["doorway_rationale"] == expected_doorway["rationale"]
        assert result["processing"] == "final_visitor_boundary_archive_examples_evidence_limits"


def test_archive_examples_evidence_limits_detector_does_not_capture_ordinary_decision_questions():
    assert not main._is_archive_examples_evidence_limits_inquiry(
        "A company has two options and must decide which change to implement. What outcome should it prioritize?"
    )
    assert not main._is_archive_examples_evidence_limits_inquiry(
        "What does the Archive say about the meaning of stewardship?"
    )
