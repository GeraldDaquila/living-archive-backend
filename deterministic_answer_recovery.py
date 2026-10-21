"""Bounded provider-independent recovery for The Guide."""
import re


def _clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _subject(question):
    value = _clean(question).rstrip(" ?.!;:")
    value = re.sub(
        r"^(?:please\s+)?(?:can you\s+|could you\s+)?"
        r"(?:explain|describe|discuss|analyze|analyse|help me understand|"
        r"tell me about|what is|what are|what does|why does|why do|why is|"
        r"why are|how does|how do|how can|how should|should we|should i)\s+",
        "", value, flags=re.I,
    )
    return value[:240].strip(" ,;:") or "the question you raised"


def compose_recovery(question, *, underlying_question="", desired_movement=""):
    """Offer a useful bounded response without inventing facts or sources."""
    q = _clean(question)
    if not q:
        return "What would you like to understand or work through?"
    subject = _clean(underlying_question) or _subject(q)
    lower = q.casefold()

    if re.search(r"\b(?:compare|comparison|difference|different from|versus|\bvs\b)\b", lower):
        answer = (
            f"A useful comparison of {subject} starts by judging the options on the same grounds. "
            "Look at what each is meant to achieve, how it works, who benefits or bears the costs, "
            "and what limits or risks come with it. Separate evidence-backed differences from assumptions. "
            "Without the specific options and context, I can't responsibly declare one better."
        )
    elif re.search(r"\b(?:why|what causes|reason for)\b", lower):
        answer = (
            f"To understand why {subject}, separate the immediate event from the conditions that made it more likely. "
            "Consider the evidence for each explanation, the incentives and constraints involved, and what other "
            "explanation could fit the same facts. These are ways to investigate the question, not conclusions "
            "about a particular case; a confident answer needs the relevant details."
        )
    elif re.search(r"\b(?:how|steps|approach|what can i do|what should we do|how to)\b", lower):
        answer = (
            f"A practical way to approach {subject} is to define the outcome you want, identify the main constraint, "
            "and choose one step small enough to test. Before acting, consider who else is affected and what could "
            "go wrong. Check the result against the original goal and adjust rather than assuming the first attempt "
            "must be final."
        )
    elif re.search(r"\b(?:should i|should we|is it worth|whether to|decision|decide)\b", lower):
        answer = (
            f"The decision about {subject} depends on what matters most, which consequences are reversible, "
            "and who would carry the costs. Set out realistic options, the strongest reason for and against each, "
            "and what information would change your mind. If the decision is reversible, a limited trial may be "
            "wiser than treating it as permanent; include people significantly affected before deciding."
        )
    elif re.search(r"\b(?:what is|what are|define|definition|meaning of|what does .* mean)\b", lower):
        answer = (
            f"Your question asks for a clear account of {subject}. A useful explanation should establish what the "
            "term or idea refers to, distinguish it from nearby concepts, and show how it works in a recognizable "
            "example. The precise meaning can depend on the field or context, so I won't invent a formal or "
            "Archive-specific definition without that grounding."
        )
    elif re.search(r"\b(?:meaning|make sense|understand|interpret|reflect|relationship)\b", lower):
        answer = (
            f"A useful starting point for {subject} is to separate what is known from what is inferred, then ask "
            "which distinction or tension matters most. Notice what is observable, what depends on interpretation, "
            "and what missing fact could change the picture. This keeps the inquiry open without treating every "
            "explanation as equally well supported."
        )
    else:
        answer = (
            f"The question about {subject} deserves a direct answer, not a guess presented as certainty. "
            "The most useful next step is to identify the specific claim or outcome at issue, separate established "
            "facts from assumptions, and examine what evidence would distinguish plausible explanations. I don't "
            "have enough verified context to assert a case-specific conclusion, but the inquiry need not stop here."
        )

    movement = _clean(desired_movement)
    if movement:
        answer += f" A sensible next step is to focus on {movement.rstrip('.')}."
    else:
        answer += " What detail or context would make this question most concrete for you?"
    return answer


def contract_snapshot():
    return {
        "contract_version": "v1",
        "provider_independent": True,
        "does_not_invent_archive_evidence": True,
        "question_shapes": ["comparison", "causal", "practical", "decision", "definition", "reflective", "general"],
    }


for _question in (
    "Why do communities lose trust?",
    "How can a team make a fair decision?",
    "What is institutional responsibility?",
    "Compare individual freedom and shared responsibility.",
    "What should we consider before changing a policy?",
    "Help me understand a difficult situation.",
):
    _answer = compose_recovery(_question)
    if not _answer or len(_answer) < 80:
        raise RuntimeError("Deterministic answer recovery contract failed: response too short.")
    if re.search(r"\b(?:provider bank|retrieval layer|canonical evidence|machine-facing|USE)\b", _answer, re.I):
        raise RuntimeError("Deterministic answer recovery contract failed: internal language leaked.")
