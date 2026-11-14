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
