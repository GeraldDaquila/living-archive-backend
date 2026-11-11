"""Regression tests for query-specific recovery doorway selection."""

import general_guide_composition as composition

QUESTION = "What does it mean for an AI to be an interpreter rather than an authority?"

def main():
    noisy = [{
        "title": "Law",
        "url": "https://geralddaquila.com/law/",
        "content": "Law concerns institutions, authority, rules, and public order.",
        "score": 0.99,
    }]
    assert composition._select_verified_recovery_doorway(QUESTION, noisy) == {
        "doorway_title": "", "doorway_url": ""
    }

    direct = noisy + [{
        "title": "AI, Interpretation and Human Judgment",
        "url": "https://geralddaquila.com/ai-interpretation-human-judgment/",
        "content": "How artificial intelligence can support interpretation without replacing human judgment.",
        "score": 0.71,
    }]
    result = composition._select_verified_recovery_doorway(QUESTION, direct)
    assert result["doorway_title"] == "AI, Interpretation and Human Judgment"

    unrelated_high_score = direct + [{
        "title": "Gardens",
        "url": "https://geralddaquila.com/gardens/",
        "content": "A reflection on soil, seasons, and cultivation.",
        "score": 1.0,
    }]
    result = composition._select_verified_recovery_doorway(QUESTION, unrelated_high_score)
    assert result["doorway_title"] == "AI, Interpretation and Human Judgment"

    print("DOORWAY RELEVANCE GATING QA: PASS")

if __name__ == "__main__":
    main()
