"""Bounded provider-independent recovery for The Guide."""
import re


def _clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _subject(question):
    value = _clean(question).rstrip(" ?.!;:")
    value = re.sub(
        r"^(?:please\s+)?(?:can you\s+|could you\s+)?"
        r"(?:help me understand|tell me about|explain|describe|discuss|analyze|analyse|"
        r"what happens if|what if|what is|what are|what does|why does|why do|why is|"
        r"why are|how does|how do|how can|how should|should we|should i)\s+",
        "", value, flags=re.I,
    )
    return value[:240].strip(" ,;:") or "the question you raised"


def _is_hindsight_accountability(question):
    """Recognize fair retrospective review versus hindsight blame before generic decision advice."""
    q = _clean(question).casefold()
    retrospective_frame = bool(re.search(
        r"\b(?:hindsight|in hindsight|at the time|available at the time|"
        r"what (?:was|could be) known|information available|original decision|"
        r"outcome was known|after the fact)\b", q
    ))
    accountability_frame = bool(re.search(
        r"\b(?:accountability|accountable|blam(?:e|ing)|responsib(?:le|ility)|"
        r"fairly judge|unfairly|distinguish|best decision|reasonable decision)\b", q
    ))
    implicit_frame = bool(
        re.search(r"\b(?:information available at the time|could with the information)\b", q)
        and re.search(r"\b(?:blam(?:e|ing)|accountability|unfairly|distinguish)\b", q)
    )
    return (retrospective_frame and accountability_frame) or implicit_frame


def _is_ethical_tradeoff(question):
    """Recognize competing-value dilemmas before generic how-to language."""
    q = _clean(question).casefold()
    competing_values = bool(re.search(
        r"\b(?:disagree|competing|conflict|trade.?offs?|priorit(?:y|ies)|"
        r"protect(?:ing)?|worth protecting|deeply value|important to each|"
        r"lose something|irreversible|bear the costs|fair(?:ly|ness)?)\b", q
    ))
    asks_for_judgment = bool(re.search(
        r"\b(?:how should we decide|how do we decide|what should we protect|"
        r"what if|who should decide|which should|what is fair|fair process|what does .{0,80} look like)\b", q
    ))
    return competing_values and asks_for_judgment


def compose_recovery(question, *, underlying_question="", desired_movement=""):
    """Offer a useful bounded response without inventing facts or sources."""
    q = _clean(question)
    if not q:
        return "What would you like to understand or work through?"
    subject = _clean(underlying_question) or _subject(q)
    lower = q.casefold()

    # Retrospective accountability must outrank generic decision advice:
    # evaluate process using what was knowable then, not the outcome known now.
    if _is_hindsight_accountability(q):
        answer = (
            "Genuine accountability asks whether the group made a reasonable decision with the information, "
            "constraints, and alternatives available at the time. Hindsight blame assumes that because the outcome "
            "is now known, it should have been predictable all along. A harmful result, by itself, does not prove "
            "that the original decision was irresponsible.\n\n"
            "Start by reconstructing what the group knew, what remained uncertain, which alternatives were realistically "
            "available, and whether relevant warnings or dissent were taken seriously. Ask whether the group used "
            "clear criteria, considered foreseeable risks, and listened to people who would bear the consequences. "
            "Also distinguish a reasonable choice that turned out badly from a choice made carelessly or without "
            "regard for evidence the group had a duty to consider.\n\n"
            "A reasonable decision at the time does not excuse refusing to learn afterward. Accountability means "
            "acknowledging the outcome, correcting what can be corrected, and improving the decision process without "
            "rewriting the past to make blame easier."
        )
    # Ethical conflicts must outrank generic "how" / practical-action patterns.
    elif _is_ethical_tradeoff(q):
        if re.search(r"\bstewardship\b", lower) and re.search(r"\b(?:disagree|protect)\w*\b", lower):
            answer = (
                "When people disagree about what is worth protecting, the disagreement may reflect different "
                "values, responsibilities, or fears about what could be lost. One person may be trying to preserve "
                "continuity; another may believe change is necessary to protect people or keep something useful. "
                "Name those underlying concerns before treating the other person as careless or unreasonable.\n\n"
                "A practical next step is to ask what each person is trying to protect, who would bear the costs of "
                "each option, and which responsibilities or rights cannot simply be traded away. Separate shared "
                "facts from judgments, and look for options that preserve the most important interests while making "
                "the unavoidable trade-offs explicit.\n\n"
                "People may not reach identical priorities, and stewardship does not require pretending otherwise. "
                "They can still agree on a fair process, explain their reasons, consider people affected but not "
                "represented, and review the decision when new evidence or consequences emerge. The aim is to handle "
                "disagreement responsibly, not to erase it."
            )
        else:
            answer = (
                "When protecting one important thing puts something else at risk, the decision cannot be made fairly "
                "by asking only which priority matters more. We also need to consider who depends on each choice, "
                "who has the power to decide, and who will bear the consequences.\n\n"
                "Make each person's claim visible, including the needs of people who may not have a voice in the "
                "decision. Distinguish losses that can be repaired from those that cannot, and examine whether a "
                "different approach could protect at least part of what matters to each side. Shared facts, clear "
                "criteria, and a chance for affected people to challenge assumptions make the process more defensible.\n\n"
                "Sometimes a genuine trade-off remains. In that case, responsibility means explaining the reasons for "
                "the decision, acknowledging what is being sacrificed, and checking that the burden does not fall "
                "unfairly on those with the least power. The question is not only what we choose to protect, but "
                "whether we can justify that choice to the people who must live with its consequences."
            )
    elif re.search(r"\b(?:compare|comparison|difference|different from|versus|vs)\b", lower):
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
    elif re.search(r"\b(?:should i|should we|is it worth|whether to|decision|decide)\b", lower):
        answer = (
            f"The decision about {subject} depends on what matters most, which consequences are reversible, "
            "and who would carry the costs. Set out realistic options, the strongest reason for and against each, "
            "and what information would change your mind. If the decision is reversible, a limited trial may be "
            "wiser than treating it as permanent; include people significantly affected before deciding."
        )
    elif re.search(r"\b(?:how|steps|approach|what can i do|what should we do|how to)\b", lower):
        answer = (
            f"A practical way to approach {subject} is to define the outcome you want, identify the main constraint, "
            "and choose one step small enough to test. Before acting, consider who else is affected and what could "
            "go wrong. Check the result against the original goal and adjust rather than assuming the first attempt "
            "must be final."
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
    if movement and not _is_ethical_tradeoff(q) and not _is_hindsight_accountability(q):
        answer += f" A sensible next step is to focus on {movement.rstrip('.')}."
    elif not _is_ethical_tradeoff(q) and not _is_hindsight_accountability(q):
        answer += " What detail or context would make this question most concrete for you?"
    return answer


def contract_snapshot():
    return {
        "contract_version": "v2",
        "provider_independent": True,
        "does_not_invent_archive_evidence": True,
        "question_shapes": ["hindsight_accountability", "ethical_tradeoff", "comparison", "causal", "decision", "practical", "definition", "reflective", "general"],
    }


for _question in (
    "Why do communities lose trust?",
    "How can a team make a fair decision?",
    "What is institutional responsibility?",
    "Compare individual freedom and shared responsibility.",
    "What should we consider before changing a policy?",
    "Help me understand a difficult situation.",
    "What does stewardship look like when people disagree about what is worth protecting?",
    "What if each person sincerely believes they are protecting something important, but protecting one person's priorities means another person will lose something they deeply value? How should we decide what to protect?",
):
    _answer = compose_recovery(_question)
    if not _answer or len(_answer) < 80:
        raise RuntimeError("Deterministic answer recovery contract failed: response too short.")
    if re.search(r"\b(?:provider bank|retrieval layer|canonical evidence|machine-facing|USE)\b", _answer, re.I):
        raise RuntimeError("Deterministic answer recovery contract failed: internal language leaked.")

_tradeoff_answer = compose_recovery(
    "What if each person sincerely believes they are protecting something important, but protecting one person's priorities means another person will lose something they deeply value? How should we decide what to protect?"
)
if "repaired" not in _tradeoff_answer or "least power" not in _tradeoff_answer:
    raise RuntimeError("Ethical trade-off recovery contract failed: missing loss and power analysis.")
if "choose one step small enough to test" in _tradeoff_answer:
    raise RuntimeError("Ethical trade-off recovery contract failed: generic practical branch won classification.")
