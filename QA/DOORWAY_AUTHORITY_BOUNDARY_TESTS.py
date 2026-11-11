"""Regression tests for the single public doorway authority boundary."""

from guide_direct_attribute_evidence import select_authoritative_doorway

QUESTION = "What does it mean for an AI to be an interpreter rather than an authority?"

def main():
    calls = []

    def reject_unrelated(query, context):
        calls.append(query)
        return None

    result = select_authoritative_doorway(
        QUESTION,
        {"title": "Law", "url": "https://geralddaquila.com/law/"},
        reject_unrelated,
        {},
        normalize=lambda value: value,
    )
    assert calls == [QUESTION]
    assert result is None, "A preselected page must not bypass relevance authority."

    def select_relevant(query, context):
        return {
            "title": "AI, Interpretation and Human Judgment",
            "url": "https://geralddaquila.com/ai-interpretation-human-judgment/",
        }

    result = select_authoritative_doorway(
        QUESTION,
        {"title": "Law", "url": "https://geralddaquila.com/law/"},
        select_relevant,
        {},
        normalize=lambda value: value,
    )
    assert result["title"] == "AI, Interpretation and Human Judgment"

    print("DOORWAY AUTHORITY BOUNDARY QA: PASS")

if __name__ == "__main__":
    main()
