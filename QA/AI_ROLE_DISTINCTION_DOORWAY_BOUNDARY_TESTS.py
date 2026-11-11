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
