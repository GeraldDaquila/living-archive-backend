"""Provider-independent four-movement fractal for relational questions.

Canonical sequence: OBSERVATION -> IMPLICATION -> SO WHAT? -> INQUIRY.
This is a bounded deterministic fallback for cases where the normal LLM path
is unavailable. It does not replace the normal LLM-first HRN composition path.

Design rules:
- Ground the observation in the visitor's own words; do not invent events.
- Treat implications as possibilities, never claims about another person's motive.
- Make "So what?" name the human stake without prescribing a decision.
- End with one answerable, context-specific inquiry.
- Return None when the question is outside the narrow supported scope.
"""
import re

CONTRACT_VERSION = "v2"
STAGES = ["observation", "implication", "so_what", "inquiry"]

_RELATION_TERMS = re.compile(
    r"\b(?:friend|friendship|partner|relationship|colleague|family|sibling|"
    r"husband|wife|spouse|parent|child|coworker|teammate)\b", re.I
)
_SIGNAL_PATTERNS = (
    (re.compile(r"\b(?:reach(?:ing)? out|initiat\w*|contact|text(?:ing)?|message(?:s|d|ing)?|"
                r"call(?:ing|s|ed)?|check(?:ing)? in|arrang(?:e|ing|ed) (?:another )?(?:time|plan)|"
                r"cancel(?:led|ed|ling|ing)? plans?)\b", re.I), "contact"),
    (re.compile(r"\b(?:distant|distance|withdraw\w*|go(?:es|ing)? quiet|silent|silence|"
                r"stop(?:ped|ping)? responding|not respond\w*|rarely reply|rarely reach)\b", re.I), "distance"),
    (re.compile(r"\b(?:argument|argue|fight|conflict|disagreements?|criticiz\w*|blam\w*|"
                r"defensive|shut down|go(?:es|ing)? quiet)\b", re.I), "conflict"),
    (re.compile(r"\b(?:chores|housework|workload|responsibilit\w*|doing all the work|"
                r"carry(?:ing)? (?:the )?load)\b", re.I), "workload"),
    (re.compile(r"\b(?:listen\w*|hear(?:ing)? me|unheard|dismiss\w*|ignore\w*)\b", re.I), "being heard"),
    (re.compile(r"\b(?:effort|one[- ]sided|reciprocat\w*|mutual|overgiv\w*|"
                r"giving more|unbalanced|imbalance)\b", re.I), "mutual effort"),
)
_MOTIVE_ASSERTION = re.compile(
    r"\b(?:they don't care|they do not care|they hate me|they are narcissists?|"
    r"they are manipulating me|they are definitely|this proves they)\b", re.I
)


def _clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _sentences(text):
    return [s.strip(" \t\r\n-") for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _specific_observation(q, sentences, signals):
    candidates = [
        sentence for sentence in sentences
        if any(pattern.search(sentence) for pattern, _ in _SIGNAL_PATTERNS)
    ]
    if candidates:
        sentence = min(candidates, key=len)
        if not _MOTIVE_ASSERTION.search(sentence):
            return sentence.rstrip(".!?")
    if signals:
        return q.rstrip(".!?")
    return ""


def compose_relational_fractal(query):
    """Return a four-movement response for supported relational questions.

    The function is deliberately conservative. It returns None for unrelated,
    too-short, or underspecified input so existing fallback behavior can handle it.
    """
    q = _clean(query)
    if len(q) < 18 or not _RELATION_TERMS.search(q):
        return None

    sentences = _sentences(q)
    matched = [label for pattern, label in _SIGNAL_PATTERNS if pattern.search(q)]
    if not matched:
        return None

    observation = _specific_observation(q, sentences, matched)
    if not observation:
        return None

    signal_set = set(matched)
    if "conflict" in signal_set or "workload" in signal_set:
        implication = (
            "That may point to a recurring difference in how the situation is experienced or handled; "
            "the details here do not establish either person's intention or the whole cause."
        )
        stake = (
            "The question underneath may be how the two of you can name what is happening "
            "without turning the conversation into a contest over who is at fault."
        )
        inquiry = (
            "Just before this pattern takes over, what is the first thing each of you seems to be "
            "trying to get across?"
        )
    elif "being heard" in signal_set:
        implication = (
            "This may leave a gap between what you are trying to communicate and what the other person "
            "takes in; it does not, by itself, tell us why that gap occurs."
        )
        stake = (
            "What matters is whether there is room for your experience to be understood without "
            "having to intensify it just to be taken seriously."
        )
        inquiry = (
            "Can you recall one recent moment when you felt unheard, and what you most wanted the other "
            "person to understand then?"
        )
    elif "distance" in signal_set or "contact" in signal_set or "mutual effort" in signal_set:
        implication = (
            "This may suggest an imbalance in how the connection is being maintained, but it does not "
            "by itself tell us why; circumstances, habits, and willingness remain distinct possibilities."
        )
        stake = (
            "The important issue may be whether the connection feels mutual enough for you to keep "
            "investing in it without feeling solely responsible for keeping it alive."
        )
        inquiry = (
            "When you notice this pattern, what feels most important to understand: what may be happening "
            "for the other person, or what balance would feel sustainable for you?"
        )
    else:
        implication = (
            "This may indicate a difference in how the relationship is being experienced, but the "
            "information given does not establish the other person's motive."
        )
        stake = (
            "The human question is what this pattern means for your sense of connection, trust, or room "
            "to be yourself within the relationship."
        )
        inquiry = (
            "Which part of this pattern matters most to you right now, and what makes that part stand out?"
        )

    response = "\n\n".join((observation + ".", implication, stake, inquiry))
    return {
        "response": response,
        "doorway_title": "",
        "provider": "deterministic_relational_fractal_v2",
        "model": "",
        "fractal_contract": CONTRACT_VERSION,
        "fractal_stages": list(STAGES),
        "fractal_evidence": {
            "matched_signals": sorted(signal_set),
            "observation_grounded_in_query": True,
            "motive_inference": False,
            "question_count": response.split("\n\n")[-1].count("?"),
        },
    }
