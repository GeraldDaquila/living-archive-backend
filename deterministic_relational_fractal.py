"""Provider-independent four-movement fractal for lived relational inquiries.

Canonical sequence: OBSERVATION -> IMPLICATION -> SO WHAT? -> INQUIRY.
This is a bounded deterministic fallback, not a replacement for specialist HRN
or the normal LLM-first composition path.
"""
import re

CONTRACT_VERSION = "v1"


def compose_relational_fractal(query):
    """Return a grounded four-movement response for clear relational-effort questions.

    Returns None outside this narrow class so ordinary questions retain the
    existing deterministic fallback behavior.
    """
    q = re.sub(r"\s+", " ", str(query or "")).strip()
    normalized = q.casefold()
    relationship = bool(re.search(r"\b(?:friend|friendship|partner|relationship|colleague|family|sibling)\b", normalized))
    effort_pattern = bool(re.search(
        r"\b(?:initiati\w*|reach(?:ing)? out|contact|distant|distance|reply|repl(?:y|ies)|"
        r"effort|one[- ]sided|reciprocat\w*|stop trying|carry(?:ing)? (?:the )?relationship)\b",
        normalized,
    ))
    if not (relationship and effort_pattern):
        return None

    observation = (
        "What you can observe is the pattern you described: you are making more of the effort to stay in contact, "
        "while the other person still responds at least some of the time."
    )
    implication = (
        "That can suggest an imbalance in who is keeping the connection active, but it does not by itself tell us why. "
        "Their circumstances, communication habits, and level of investment are all still open questions."
    )
    so_what = (
        "The important issue may be less about counting messages and more about whether the relationship feels mutual "
        "enough for you to keep tending it without feeling solely responsible for its survival."
    )
    inquiry = (
        "When you give the other person room to initiate, what do you most want to understand: whether they want the connection, "
        "or what kind of balance would feel sustainable for you?"
    )
    return {
        "response": "\n\n".join((observation, implication, so_what, inquiry)),
        "doorway_title": "",
        "provider": "deterministic_relational_fractal_v1",
        "model": "",
        "fractal_contract": CONTRACT_VERSION,
        "fractal_stages": ["observation", "implication", "so_what", "inquiry"],
    }
