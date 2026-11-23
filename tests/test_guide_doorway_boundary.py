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
