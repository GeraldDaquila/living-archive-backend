"""Bounded response contract for leadership questions about extractive incentives.

The contract addresses a narrow, repeatable task: a leader asks how to respond
when institutional incentives reward short-term extraction. It treats this as
an incentive/governance design problem, not an individual-morality diagnosis.
"""

from __future__ import annotations

import re


def is_institutional_extraction_incentives_question(question: str) -> bool:
    """Recognize the combined leadership, incentive, and extraction problem."""
    text = re.sub(r"\s+", " ", str(question or "")).strip().casefold()
    leadership = bool(re.search(
        r"\b(?:leader|leadership|executive|board|governor|director|manager)\b", text
    ))
    institutional = bool(re.search(
        r"\b(?:institution|institutional|organization|organisational|organizational|governance|system)\b",
        text,
    ))
    incentive = bool(re.search(
        r"\b(?:incentive|incentives|reward|rewards|rewarded|rewarding|metric|metrics|target|targets|"
        r"compensation|bonus|promotion|performance measure)\b",
        text,
    ))
    extraction = bool(re.search(
        r"\b(?:extract|extraction|extractive|depletion|deplete|short[- ]term|immediate returns?|"
        r"quarterly gains?|externaliz\w* costs?)\b",
        text,
    ))
    action = bool(re.search(
        r"\b(?:how should|what should|how can|what can|respond|response|address|change|reform)\b",
        text,
    ))
    return leadership and institutional and incentive and extraction and action


def recovery_response() -> str:
    """Provide a complete, provider-independent answer for the recognized task."""
    return (
        "Treat the pattern as an incentive-design problem, not simply a failure of individual virtue. "
        "When promotion, budgets, compensation, political credit, or performance measures reward immediate "
        "returns while costs are pushed onto workers, communities, public trust, or the ecological base, "
        "people adapt to the signals the institution actually sends. Appeals to better values will have "
        "limited effect if the operating rules continue to reward depletion.\n\n"
        "First make the extraction loop visible: identify what is rewarded, what is being depleted, who "
        "captures the gains, who carries the delayed costs, what information is missing, and who has the "
        "authority to challenge the pattern. Then redesign the rules together: balance short-term outputs "
        "with measures of long-term capacity and replenishment; align decision authority with responsibility "
        "for displaced costs; include the people who bear those costs; protect dissent and independent review; "
        "and establish review points with clear conditions for changing or stopping a policy. Do not merely "
        "add long-term targets on top of unchanged short-term rewards, because conflicting measures invite "
        "gaming rather than correction.\n\n"
        "Make the change testable. Pilot the revised incentives, publish who owns each commitment, and track "
        "results over an appropriate time horizon: output alongside staff capability, trust, maintenance, "
        "distribution of benefits and burdens, and relevant social or ecological effects. Compare these "
        "signals with a baseline and revise when evidence shows continued depletion. If the leader cannot "
        "change the incentives alone, the responsible move is to make the conflict visible to the board or "
        "governing authority and seek a clear mandate—not to imply that personal resolve can overcome an "
        "unchanged institutional design. The aim is to move from extraction toward circulation and renewal "
        "while preserving genuinely useful production."
    )


def canonical_doorway() -> dict[str, str]:
    """Return the verified public Archive continuation for this exact question family."""
    return {
        "title": "Regenerative Governance: What Comes After Extraction-Based Systems?",
        "url": (
            "https://geralddaquila.com/2026/06/08/"
            "regenerative-governance-what-comes-after-extraction-based-systems/"
        ),
        "rationale": (
            "This essay examines institutions organized around extraction and the "
            "governance conditions needed to regenerate trust, capacity, participation, "
            "resilience, and long-term human flourishing. It is a direct continuation "
            "for a leader asking how to respond to incentives that reward short-term "
            "gains while weakening the system's foundations."
        ),
    }
