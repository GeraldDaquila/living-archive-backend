"""Question-specific operational completion contract for nonprofit burnout inquiries."""
import re


def is_nonprofit_mission_care_question(question: str) -> bool:
    low = " ".join(str(question or "").casefold().split())
    nonprofit = bool(re.search(r"\bnonprofit|non-profit|charit(?:y|ies)|mission[- ]driven organization\b", low))
    burnout = bool(re.search(r"\bburn(?:out|ed|ing out)|staff exhaustion|staff wellbeing|staff well-being|workload strain\b", low))
    systems = bool(re.search(r"\b(care|structure|purpose|mission|operational|capacity|workload)\b", low))
    return nonprofit and burnout and systems


def build_nonprofit_mission_care_instruction(question: str) -> str:
    if not is_nonprofit_mission_care_question(question):
        return ""
    return (
        "NONPROFIT MISSION-CARE OPERATIONAL COMPLETION: Do not stop after naming the "
        "relationship among purpose, care, structure, and capacity. Distinguish essential "
        "mission commitments from accumulated activity; explain institutional care, role "
        "and decision-right alignment, and funded capacity including hidden work. Treat "
        "burnout feedback loops as hypotheses to investigate, not universal diagnoses. "
        "Give an actionable sequence: stabilize immediate overload and protect staff voice; "
        "map commitments, workload, staffing, funding, authority, and hidden work; identify "
        "the capacity gap; make explicit stop/defer/simplify/redistribute/fund/phase tradeoffs; "
        "redesign roles and escalation; assign owners and resources; review with staff and "
        "governance and revise when evidence changes. End with one concrete next action "
        "such as a staff-informed capacity-and-commitment map. Do not invent a resource URL "
        "or present a visible resource title as a verified destination."
    )
