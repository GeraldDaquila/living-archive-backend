"""Regression QA for the earned communication/listening focus in HRN-to-USE return."""
import main


def main_test():
    original = "I want to understand a friendship where I feel unheard when we disagree."
    need = "I want to be heard during disagreement."
    delta = "A counterpoint is a distinct relational move, not just a failure to listen."
    anchor = main._relational_return_topic_anchor(original, need, delta)
    assert "Relational communication during disagreement" in anchor
    assert "listening" in anchor and "being heard" in anchor

    query = original + " The counterpoint arrives before my view feels heard."
    grounded_resource = {
        "title": "Sacred Exchange",
        "text": (
            "Friendship and relationships depend on listening, acknowledgment, and communication. "
            "During disagreement, people can respond to one another before they have heard the point being made."
        ),
    }
    assert main._relational_return_earned_focus_fit(query, grounded_resource), (
        "A canonical resource grounded in listening and relational communication should qualify."
    )

    weak_resource = {
        "title": "Learning to Receive Without Feeling Guilty",
        "text": "This essay discusses generosity, receiving help, guilt, and giving more than one receives.",
    }
    assert not main._relational_return_earned_focus_fit(query, weak_resource), (
        "Receiving/giving themes alone must not qualify for a listening/disagreement journey."
    )

    unrelated_query = "What is the capital city of Japan and what is its population?"
    assert not main._relational_return_earned_focus_fit(unrelated_query, grounded_resource), (
        "An unrelated factual lookup must not qualify for a relational doorway."
    )
    print("V489.104 HRN RELATIONAL COMMUNICATION RETURN QA: PASS")


if __name__ == "__main__":
    main_test()
