"""Visitor-facing doorway regression tests."""
import asyncio
import json


async def _capture_json_boundary(payload):
    import main
    events = []

    async def send(event):
        events.append(event)

    await main._use_send_json(send, payload)
    body = next(event["body"] for event in events if event["type"] == "http.response.body")
    return json.loads(body.decode("utf-8"))


def test_organizational_learning_doorway_survives_final_visitor_boundary():
    result = asyncio.run(_capture_json_boundary({
        "query": "How do organizations create conditions for learning from failure?",
        "response": "stale answer without navigation",
        "recommendation": None,
    }))
    doorway = result["recommendation"]
    assert doorway["title"] == "The Social Architecture of Thriving: Conditions That Allow Human Potential to Expand"
    assert doorway["url"] == "https://geralddaquila.com/2026/06/15/the-social-architecture-of-thriving-conditions-that-allow-human-potential-to-expand/"
    assert result["canonical_doorway"] == doorway


def test_community_rule_design_selects_verified_barangay_governance_doorway_before_generic_candidates():
    import main

    query = "How should a community decide whether limits on personal liberty are justified by shared obligations and risks?"
    expected = {
        "title": "The Barangay Before the State: Human-Scale Governance in Practice",
        "url": "https://geralddaquila.com/2026/09/21/the-barangay-before-the-state-human-scale-governance-in-practice/",
    }

    selected = main._community_rule_design_canonical_doorway(query)
    assert selected["title"] == expected["title"]
    assert selected["url"] == expected["url"]
    assert "community decision-making" in selected["rationale"]
    assert main._general_guide_authoritative_doorway(
        query, {"_doorway_selection_trace": {}}
    )["url"] == expected["url"]
    assert main._boundary_canonical_doorway(
        {"recommendation": None}, query
    )["url"] == expected["url"]
    assert main._verified_archive_doorway_fallback(
        query,
        [{"title": "ARK-004: Post-Fiat Trade — The Community Ledger SOP",
          "url": "https://geralddaquila.com/2026/05/02/ark-004-post-fiat-trade-the-community-ledger-sop/",
          "text": "A community ledger for post-fiat trade and exchange."}],
        {"risk": True, "action": "risk"},
    )["url"] == expected["url"]


def test_community_rule_doorway_family_does_not_capture_post_fiat_ledger_questions():
    import main

    query = "How should a community use a shared ledger to exchange goods in a post-fiat economy?"
    assert main._community_rule_design_canonical_doorway(query) is None


def test_unmapped_risk_query_does_not_receive_a_late_generic_doorway():
    import main

    query = "What should I do if I face immediate physical danger?"
    candidate = {
        "title": "ARK-004: Post-Fiat Trade — The Community Ledger SOP",
        "url": "https://geralddaquila.com/2026/05/02/ark-004-post-fiat-trade-the-community-ledger-sop/",
        "text": "A community ledger for post-fiat trade and exchange.",
    }
    assert main._verified_archive_doorway_fallback(
        query, [candidate], {"risk": True, "action": "risk"}
    ) is None


def test_abstract_consequential_uncertainty_keeps_its_verified_doorway():
    import main

    query = "How should I make responsible choices when consequences matter but the future is uncertain?"
    doorway = main._verified_archive_doorway_fallback(
        query, [], main._base._inquiry_profile(query)
    )
    assert doorway is not None
    assert doorway["title"] == "Sovereign Sensemaking Compass"
    assert doorway["url"] == "https://geralddaquila.com/the-sovereign-sensemaking-compass/"




def test_explicit_send_me_to_another_page_instruction_is_terminal_at_json_boundary():
    query = "Explain stewardship, but do not send me to another page yet."
    assert __import__("main")._guide_query_explicitly_forbids_handoff(query)
    result = asyncio.run(_capture_json_boundary({
        "query": query,
        "response": (
            "Stewardship means caring for what is entrusted to you.\n\n"
            "It matters because ordinary choices affect other people and the future.\n\n"
            "Care has limits; responsibility does not confer ownership.\n\n"
            "The available Archive material does not contain a dedicated treatment of stewardship."
        ),
        "recommendation": {
            "title": "Unrelated page",
            "url": "https://example.org/unrelated",
            "rationale": "An incidental recommendation.",
        },
    }))
    assert result["recommendation"] is None
    assert result["doorway_decision"] == "omit"
    assert len(result["response"].split("\\n\\n")) == 3


def test_explicit_no_doorway_request_overrides_community_rule_family_mapping():
    import main

    query = (
        "How should a community decide whether limits on personal liberty are justified "
        "by shared obligations and risks? Please don't include links or resources."
    )
    assert main._select_verified_doorway_conceptual_family(query) is None
    assert main._general_guide_authoritative_doorway(
        query, {"_doorway_selection_trace": {}}
    ) is None
    assert main._select_guide_node_fallback_doorway(query) is None
    assert main._verified_archive_doorway_fallback(
        query, [], {"risk": True, "action": "risk"}
    ) is None
    assert main._boundary_canonical_doorway(
        {"recommendation": None}, query
    ) is None
