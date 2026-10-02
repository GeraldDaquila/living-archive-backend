"""Static contract tests for the HRN visitor-response policy.

These tests mirror the policy implemented in the HRN plugin and are intentionally
provider-independent. They ensure that the key behavioral categories remain
blocked/allowed as the integration evolves.
"""

import re


DIRECTIVE_PATTERNS = (
    re.compile(r"\byou\s+(?:should|must|need to|have to|ought to|are supposed to)\b", re.I),
    re.compile(r"\byou\s+(?:might|could|can|may)\s+try\b", re.I),
    re.compile(
        r"\byou\s+(?:need|have)\s+to\s+"
        r"(?:talk|ask|tell|leave|stay|set|change|stop|start|contact|call|reach|write|say|do|make|avoid|create|invite|confront|forgive|accept|let)\b",
        re.I,
    ),
    re.compile(
        r"\byou\s+(?:try|consider|choose|decide|start|stop|avoid|leave|stay|contact|call|reach out|talk to|tell|ask|say|write|set|change|make|invite|confront)\b",
        re.I,
    ),
    re.compile(r"\b(?:i|we)\s+(?:recommend|advise|suggest)\s+(?:you|that you)\b", re.I),
    re.compile(r"\b(?:the|your)\s+(?:best|right|next)\s+(?:thing|step|move|choice|decision)\s+(?:is|would be)\b", re.I),
    re.compile(r"\b(?:a|an)\s+(?:good|helpful|healthy|wise)\s+(?:next|first)\s+(?:step|thing|move|choice)\s+(?:is|would be)\b", re.I),
    re.compile(r"\b(?:what you should do|what you need to do|what you must do|what you ought to do)\b", re.I),
    re.compile(r"\b(?:do not|don't)\s+(?:stay|leave|contact|call|talk|ask|tell|try|forgive|change|ignore|respond|engage|return|go|make)\b", re.I),
    re.compile(
        r"(?:^|[.!?]\s+)\s*(?:try|consider|avoid|stop|start|tell|ask|call|contact|leave|stay|go|write|say|set|change|make|invite|forgive)\s+"
        r"(?:the|a|an|your|them|him|her|it|someone|anyone|people|this|that)\b",
        re.I,
    ),
)

MOTIVE_OR_LABEL_PATTERNS = (
    "your partner is a narcissist",
    "they are a narcissist",
    "he is a narcissist",
    "she is a narcissist",
    "they are toxic",
    "he is toxic",
    "she is toxic",
    "they are abusive",
    "he is abusive",
    "she is abusive",
    "they are manipulating you",
    "he is manipulating you",
    "she is manipulating you",
)


def blocked(text: str) -> bool:
    low = re.sub(r"\s+", " ", text.strip().lower())
    return any(p.search(low) for p in DIRECTIVE_PATTERNS) or any(x in low for x in MOTIVE_OR_LABEL_PATTERNS)


def run() -> None:
    prohibited = [
        "You should leave the relationship.",
        "You might try talking to them calmly.",
        "Consider setting a boundary.",
        "I recommend that you speak with them.",
        "The next step is to call someone you trust.",
        "You need to stop answering these messages.",
        "Try asking them what they want.",
        "Do not stay in that relationship.",
    ]
    accepted = [
        "Something changes when the wish to be understood becomes stronger than the wish to be right.",
        "You may be noticing a difference between what you intended and what they experienced.",
        "What changes when you see the moment from their side?",
        "There is a tension here between closeness and the freedom to remain yourself.",
    ]

    for text in prohibited:
        assert blocked(text), f"policy failed to block: {text!r}"

    for text in accepted:
        assert not blocked(text), f"policy incorrectly blocked: {text!r}"

    print("HRN visitor-response policy tests: PASS")


if __name__ == "__main__":
    run()
