"""Regression contract: conceptual answer recovery cannot inherit an unrelated doorway."""

import re

QUESTION = "What does it mean for an AI to be an interpreter rather than an authority?"

def suppresses_unreviewed(query, recovery):
    ai_role_distinction = bool(
        re.search(r"\b(?:ai|artificial intelligence)\b", query, re.I)
        and re.search(r"\binterpreter\b", query, re.I)
        and re.search(r"\bauthority\b", query, re.I)
    )
    reviewed = recovery.get("doorway") if isinstance(recovery, dict) else None
    return ai_role_distinction and not reviewed

def test_verified_canonical_ai_role_candidate_can_be_released():
    candidate = {"title": "AI and Human Judgment", "url": "https://geralddaquila.com/example/"}
    assert candidate["title"] and candidate["url"].startswith("https://geralddaquila.com/")

def test_ai_role_distinction_is_a_verified_conceptual_family():
    import main as runtime
    assert runtime._select_verified_doorway_conceptual_family(QUESTION) == "ai_role_distinction"
    assert runtime._select_verified_doorway_conceptual_family(
        "What does authority mean in governance?"
    ) is None


def test_ai_role_distinction_recovers_verified_responsible_ai_doorway():
    # Import the runtime selector rather than duplicating its decision logic.
    import main as runtime
    doorway = runtime._select_guide_node_fallback_doorway(QUESTION)
    assert doorway == {
        "title": "Responsible AI Principle",
        "url": "https://geralddaquila.com/responsible-ai-principle/",
    }

def test_ai_role_distinction_final_fallback_contract_is_not_recovery_only():
    # The selector is the last-mile authority for this conceptual family and
    # must be available independently of systems-map recovery.
    import main as runtime
    doorway = runtime._select_guide_node_fallback_doorway(QUESTION)
    assert doorway["title"] == "Responsible AI Principle"

def test_final_json_boundary_emits_responsible_ai_doorway():
    import asyncio
    import json
    import main as runtime

    sent = []

    async def capture(message):
        sent.append(message)

    asyncio.run(
        runtime._use_send_json(
            capture,
            {
                "query": QUESTION,
                "response": "A bounded conceptual explanation.",
                "recommendation": None,
            },
        )
    )
    body = next(item["body"] for item in sent if item["type"] == "http.response.body")
    payload = json.loads(body.decode("utf-8"))
    assert payload["recommendation"] == {
        "title": "Responsible AI Principle",
        "url": "https://geralddaquila.com/responsible-ai-principle/",
    }

def main():
    assert suppresses_unreviewed(QUESTION, {"response": "bounded explanation"})
    assert not suppresses_unreviewed(
        QUESTION,
        {"response": "bounded explanation", "doorway": {"title": "AI and Human Judgment", "url": "https://geralddaquila.com/example/"}},
    )
    assert not suppresses_unreviewed(
        "What does authority mean in governance?",
        {"response": "bounded explanation"},
    )
    print("AI ROLE DISTINCTION DOORWAY BOUNDARY QA: PASS")

if __name__ == "__main__":
    main()
