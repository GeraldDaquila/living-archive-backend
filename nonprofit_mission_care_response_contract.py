"""Deterministic completion contract for nonprofit mission-care questions."""
import re

def is_nonprofit_mission_care_question(question: str) -> bool:
    low = " ".join(str(question or "").casefold().split())
    nonprofit = bool(re.search(r"\b(?:nonprofit|non-profit|charit(?:y|ies)|mission-driven organization)\b", low))
    burnout = bool(re.search(r"\b(?:burnout|burned out|burning out|staff exhaustion|staff wellbeing|staff well-being|workload strain)\b", low))
    systems = bool(re.search(r"\b(?:care|structure|purpose|mission|operational|capacity|workload)\b", low))
    return nonprofit and burnout and systems

def evaluate_nonprofit_mission_care_response(question: str, response: str) -> dict:
    applies = is_nonprofit_mission_care_question(question)
    if not applies:
        return {"applies": False, "passed": True, "missing": []}
    text = " ".join(str(response or "").casefold().split())
    checks = {
        "immediate_staff_protection_and_voice": r"\b(?:stabiliz|protect|pause|reduce|reliev|limit|safeguard)\w*.{0,180}\b(?:staff|people|workload|overload|voice|input)\b|\b(?:staff|people)\b.{0,140}\b(?:voice|input|speak|raise concerns|overload)\b",
        "commitment_capacity_mapping": r"\b(?:map|audit|inventory|compare|review|document)\w*.{0,180}\b(?:commitments|workload|staffing|capacity|funding|resources|hidden work)\b",
        "explicit_operational_tradeoffs": r"\b(?:stop|defer|simplify|redistribute|fund|phase|prioriti[sz]e|reduce)\b.{0,180}\b(?:work|activity|commitment|service|scope|load|program|capacity)\b|\b(?:trade-?offs?|decide what to stop|defer or simplify|redistribute work)\b",
        "roles_authority_and_accountability": r"\b(?:role|responsibilit|authority|decision rights|owner|accountab|escalat)\w*\b",
        "resourced_review_and_feedback": r"\b(?:review|revisit|check|monitor|feedback|staff-informed|governance)\b.{0,180}\b(?:staff|people|capacity|workload|governance|evidence|progress)\b|\b(?:staff|people)\b.{0,180}\b(?:feedback|review|revisit|check)\b",
        "concrete_next_action": r"\b(?:start|begin|first|next|within|this week|today)\b.{0,180}\b(?:map|audit|list|document|convene|meet|review|identify|compare)\w*\b",
    }
    missing = [name for name, pattern in checks.items() if not re.search(pattern, text, re.I)]
    if len(text.split()) < 100:
        missing.append("substantive_operational_depth")
    return {"applies": True, "passed": not missing, "missing": missing}

def recover_nonprofit_mission_care_response() -> str:
    return (
        "A nonprofit can be deeply committed to its mission and still exhaust its staff when commitments exceed the people, time, funding, authority, and systems available to carry them. The first task is not to ask staff to become more resilient; it is to make the institution's real workload and capacity visible. Burnout, turnover, or cynicism may signal a structural gap, but the organization should investigate rather than assume one explanation fits everyone.\n\n"
        "Start by stabilizing immediate overload: protect time for essential work, pause avoidable demands where possible, and give staff a safe, consequential way to describe what is unsustainable. Then map the organization's mission commitments against actual services, workload, staffing, funding, decision authority, and hidden work such as emotional labor, coordination, and compliance. Compare the map with staff experience; a budget or org chart alone will not reveal the whole load.\n\n"
        "Use that evidence to make explicit choices. Decide what to protect, stop, defer, simplify, redistribute, fund, or phase rather than treating every activity as equally urgent. Clarify who can make those decisions, who owns each priority, how staff can escalate unsafe or unworkable demands, and what resources accompany new responsibilities. Care becomes institutional when workload limits, decision rights, supervision, recovery time, and staff voice are built into ordinary operating decisions—not left to individual goodwill.\n\n"
        "Finally, review the changes with staff and governance at an agreed interval. Track workload, vacancies, turnover, missed commitments, and staff-reported conditions, while treating those signals as evidence to interpret rather than as a score that tells the whole story. Assign an owner and resources to each adjustment, and revise when the evidence changes.\n\n"
        "**A practical first step:** convene a staff-informed capacity-and-commitment review. List the organization's current commitments, estimate the work and people each requires, expose hidden work, and mark each item protect, stop, defer, simplify, redistribute, or fund. Use that shared map to decide what the organization can responsibly promise next."
    )
