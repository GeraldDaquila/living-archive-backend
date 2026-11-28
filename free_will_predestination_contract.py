"""Question-specific reasoning contract for free will and predestination inquiries.

This is a bounded conceptual contract, not a claim that one theological or
philosophical position is settled. It preserves valid provider prose when the
required distinctions are present and supplies a deterministic recovery only
when the response misses the contract.
"""

import re


def is_free_will_predestination_question(question: str) -> bool:
    """Recognize inquiries that explicitly connect agency with predestination or determinism."""
    q = " ".join(str(question or "").casefold().split())
    agency = bool(re.search(
        r"\b(?:free\s+will|free\s+choice|human\s+agency|personal\s+agency)\b", q
    ))
    determination = bool(re.search(
        r"\b(?:predestination|predetermin\w*|determinism|causal\s+determinism|"
        r"causal\s+necessit\w*|programmed\s+to\s+behave|determined\s+in\s+advance)\b", q
    ))
    relationship = bool(re.search(
        r"\b(?:reconcil\w*|compatib\w*|relationship|relation|between|coexist\w*|"
        r"programmed|certain\s+way|whether|conflict|tension)\b", q
    ))
    return agency and determination and relationship


def has_free_will_predestination_explanation(response: str) -> bool:
    """Require distinct metaphysical, causal, and agency distinctions without prescribing wording."""
    text = " ".join(str(response or "").casefold().split())
    requirements = (
        (
            r"\bpredestination\b",
            r"\b(?:determinism|deterministic|causal determinism)\b",
            r"\b(?:different|distinct|not the same|not identical|not synonymous|separate)\b",
        ),
        (
            r"\bcompatibilis\w*\b",
            r"\b(?:one account|one view|some philosophers|some traditions|some thinkers|one philosophical|one position)\b",
            r"\b(?:contested|disputed|not settled|not universally accepted|not a consensus|other views|critics|disagreement)\b",
        ),
        (
            r"\b(?:coercion|coerced|external constraint|compulsion|compelled)\b",
            r"\b(?:otherwise|alternative possibilit\w*|could have done otherwise|same circumstances|same conditions|same past)\b",
        ),
        (
            r"\b(?:reason\w*|deliberat\w*|reflection|values)\b",
            r"\b(?:agency|choice|choosing|action)\b",
            r"\b(?:shaped|formed|influenced|conditioned|arise from|arising from)\b",
        ),
        (
            r"\b(?:incompatibilis\w*|libertarian free will|libertarian view)\b",
            r"\b(?:otherwise|sourcehood|ultimate source|same past|laws of nature|could have done otherwise)\b",
        ),
        (
            r"\b(?:traditions?|theolog\w*|religious frameworks?|faith traditions?)\b",
            r"\b(?:differ|var\w*|disagree|not uniform|not all|some)\b",
        ),
    )
    return len(text.split()) >= 120 and all(
        all(re.search(pattern, text) for pattern in group)
        for group in requirements
    )


def free_will_predestination_recovery() -> str:
    """Give a balanced answer when a provider misses the bounded reasoning contract."""
    return (
        "Free will and predestination can be reconciled in some philosophical and theological "
        "frameworks, but the answer depends on what each term means. Predestination is usually "
        "a theological claim about divine will, decree, or purpose. Divine foreknowledge is a "
        "related but different claim: knowing what will happen does not, by itself, establish "
        "that the knower causes it. Philosophical determinism is different again: it holds that "
        "events follow from prior conditions together with the laws or regularities of nature. "
        "Causal influence and conditioning are weaker claims still. These ideas are related, "
        "but they are not interchangeable.\n\n"
        "Compatibilism is one philosophical account. It argues that a person can act freely "
        "even in a causally determined world when the action flows from the person's own "
        "deliberation, values, and reasons rather than from coercion or external compulsion. "
        "On this view, being influenced by upbringing, biology, relationships, or circumstances "
        "does not automatically mean being forced. At the same time, those influences help form "
        "the very reasons and desires through which a person chooses. Compatibilism therefore "
        "offers an account of agency within causes; it does not show that a person is the "
        "uncaused origin of every desire or decision, and it is not a settled consensus.\n\n"
        "Incompatibilist views press a different question. If the entire past and the laws of "
        "nature fixed what happens, could the person genuinely have done otherwise under exactly "
        "those same conditions? Some argue that freedom requires such alternative possibilities "
        "or that the person must be, in a deeper sense, the source of the choice. From that "
        "perspective, determinism and the strongest form of free will are in tension. The "
        "distinction between acting without coercion and being able to choose otherwise is "
        "important: the first does not automatically settle the second.\n\n"
        "So people are not adequately described as simply 'programmed.' A causal explanation "
        "of how a choice arose does not by itself prove that the person was coerced, that "
        "deliberation is meaningless, or that responsibility disappears. But neither does the "
        "experience of choosing prove that choices are independent of prior causes. The most "
        "careful answer is that agency can be understood as real but conditioned, while the "
        "deeper question of whether that is enough for free will remains disputed. Theological "
        "traditions also differ in how they understand divine sovereignty, foreknowledge, human "
        "participation, and responsibility; there is no single account shared by all of them."
    )
