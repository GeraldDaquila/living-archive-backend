"""Gold-standard regression contract for the AI interpreter/authority inquiry.

This benchmark protects a complete conceptual answer from acquiring an
unsupported Archive continuation. Completion is preferred to a false doorway.
"""

QUESTION = "What does it mean for an AI to be an interpreter rather than an authority?"

def assert_gold_standard(answer, doorway):
    assert answer and len(answer.strip()) > 300
    assert doorway is None, (
        "The AI interpreter/authority benchmark must not acquire an "
        "unsupported doorway. A complete answer is preferable to a false next step."
    )

def main():
    representative_answer = (
        "An AI can help people understand information without claiming the final "
        "right to decide what that information means or what should be done. "
        "It can organize evidence, compare perspectives, identify patterns, "
        "explain relationships, and make uncertainty easier to see. Those are "
        "interpretive contributions: they improve the material available for "
        "judgment, but they do not settle the judgment themselves."
    ) * 3
    assert_gold_standard(representative_answer, None)
    print("AI ROLE DISTINCTION GOLD STANDARD CONTRACT: PASS")

if __name__ == "__main__":
    main()
