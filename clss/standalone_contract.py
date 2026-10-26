"""Standalone CLSS input/output contract; no USE integration or provider calls.

The nine question strings are copied verbatim from the private v0.1.0 prototype
inspected on 2026-10-27. Do not revise them without explicit approval.
"""
from __future__ import annotations

from typing import Any

CONTRACT_VERSION = "clss-reflection-v1"
PERSPECTIVES = frozenset({"self", "third_party"})
EVIDENCE_KINDS = frozenset({"observed", "reported", "inference", "unknown", "tension"})
DIMENSIONS = frozenset({
    "intention_responsibility",
    "decisions_actions",
    "relational_systemic_effects",
    "recognition_correction",
    "bounded_stewardship",
})

QUESTIONS = (
    ("q1", "What responsibility or decision are you facing?", "State the decision, the role involved, and why it matters now."),
    ("q2", "What evidence supports your current view of this person’s leadership?", "Separate direct observation, documented outcomes, testimony, reputation, and inference."),
    ("q3", "How does this person respond when resources are scarce or priorities conflict?", "Recall a specific trade-off, what they chose, who was affected, and what followed."),
    ("q4", "What happens when this person receives difficult feedback?", "Look for listening, clarification, accountability, repair, retaliation, or repeated avoidance."),
    ("q5", "What recurring effects does their leadership have on people and the wider system?", "Consider trust, clarity, capability, fairness, resilience, and long-term consequences."),
    ("q6", "What does their approach to authority and responsibility reveal?", "Describe observable behavior; do not assume motives from confidence, ambition, or reluctance alone."),
    ("q7", "Is responsibility freely accepted and mutually understood?", "Consider willingness, affected people’s consent where relevant, and clarity of expectations."),
    ("q8", "Are authority, accountability, and review conditions clearly bounded?", "Identify the scope of authority, decision rights, feedback channels, review dates, and consequences."),
    ("q9", "What remains unverified before a responsible decision can be made?", "Name the most important evidence gap and the fairest practical way to examine it."),
)

DOORWAYS = {
    "eligibility_filter": ("Eligibility Filter", "https://geralddaquila.com/leadership-selection-framework-eligibility-filter/"),
    "stewardship_evidence": ("Stewardship Evidence", "https://geralddaquila.com/leadership-selection-framework-stewardship-evidence/"),
    "simulation_testing": ("Simulation Testing", "https://geralddaquila.com/leadership-selection-framework-simulation-testing/"),
    "relational_feedback": ("Relational Feedback", "https://geralddaquila.com/leadership-selection-framework-relational-feedback/"),
    "reluctance_filter": ("Reluctance Filter", "https://geralddaquila.com/leadership-selection-framework-reluctance-filter/"),
    "consent_appointment": ("Consent Appointment", "https://geralddaquila.com/leadership-selection-framework-consent-appointment/"),
    "time_bound_stewardship": ("Time-Bound Stewardship", "https://geralddaquila.com/leadership-selection-framework-time-bound-stewardship/"),
}

class ContractError(ValueError):
    """Raised when a CLSS packet violates the deterministic contract."""


def validate_input(packet: Any) -> dict:
    if not isinstance(packet, dict):
        raise ContractError("input must be an object")
    if packet.get("contract_version") != CONTRACT_VERSION:
        raise ContractError("unsupported contract_version")
    if not isinstance(packet.get("perspective"), str) or packet.get("perspective") not in PERSPECTIVES:
        raise ContractError("perspective must be self or third_party")
    answers = packet.get("answers")
    if not isinstance(answers, list) or len(answers) != len(QUESTIONS):
        raise ContractError("answers must contain exactly nine answer records")
    seen = set()
    normalized = []
    expected_ids = {q[0] for q in QUESTIONS}
    for item in answers:
        if not isinstance(item, dict):
            raise ContractError("each answer must be an object")
        answer_id, text = item.get("answer_id"), item.get("text")
        if not isinstance(answer_id, str) or answer_id not in expected_ids or answer_id in seen:
            raise ContractError("answer IDs must be unique known IDs q1-q9")
        if not isinstance(text, str):
            raise ContractError("answer text must be a string; use empty string for unknown")
        if len(text) > 12000:
            raise ContractError("answer text exceeds 12000 characters")
        seen.add(answer_id)
        normalized.append({"answer_id": answer_id, "text": text.strip()})
    if seen != expected_ids:
        raise ContractError("all nine answer IDs must be present, including blank answers")
    return {
        "contract_version": CONTRACT_VERSION,
        "perspective": packet["perspective"],
        "answers": sorted(normalized, key=lambda a: a["answer_id"]),
    }


def validate_output(output: Any, input_packet: dict) -> dict:
    """Validate shape, answer references, and canonical destinations, not semantic truth."""
    if not isinstance(output, dict):
        raise ContractError("output must be an object")
    if output.get("contract_version") != CONTRACT_VERSION:
        raise ContractError("unsupported output contract_version")
    if output.get("perspective") != input_packet.get("perspective"):
        raise ContractError("output perspective must match input perspective")
    answer_ids = {a["answer_id"] for a in input_packet["answers"]}
    claims = output.get("evidence_map")
    if not isinstance(claims, list):
        raise ContractError("evidence_map must be a list")
    claim_ids = set()
    for claim in claims:
        if not isinstance(claim, dict):
            raise ContractError("each evidence claim must be an object")
        cid = claim.get("claim_id")
        if not isinstance(cid, str) or not cid or cid in claim_ids:
            raise ContractError("claim_id must be a unique non-empty string")
        claim_ids.add(cid)
        refs = claim.get("answer_refs")
        if not isinstance(refs, list) or not refs or not all(isinstance(ref, str) for ref in refs):
            raise ContractError("each interpretive claim requires answer references")
        if any(ref not in answer_ids for ref in refs):
            raise ContractError("claim references an absent answer ID")
        if not isinstance(claim.get("evidence_kind"), str) or claim.get("evidence_kind") not in EVIDENCE_KINDS:
            raise ContractError("invalid evidence_kind")
        if not isinstance(claim.get("coherence_dimension"), str) or claim.get("coherence_dimension") not in DIMENSIONS:
            raise ContractError("invalid coherence_dimension")
        if not isinstance(claim.get("statement"), str) or not claim["statement"].strip():
            raise ContractError("claim statement is required")
        if not isinstance(claim.get("alternative_readings"), list):
            raise ContractError("alternative_readings must be a list")
        if not isinstance(claim.get("uncertainty"), str):
            raise ContractError("uncertainty must be a string")
    for field in ("supported_coherence", "possible_incoherence", "unresolved_questions", "boundary_notes"):
        if not isinstance(output.get(field), list):
            raise ContractError(f"{field} must be a list")
    step = output.get("next_step")
    if not isinstance(step, dict) or not isinstance(step.get("action"), str) or not step["action"].strip():
        raise ContractError("next_step.action is required")
    if not isinstance(step.get("rationale"), str) or not isinstance(step.get("evidence_refs"), list):
        raise ContractError("next_step requires rationale and evidence_refs")
    if not all(isinstance(ref, str) for ref in step["evidence_refs"]) or any(ref not in answer_ids for ref in step["evidence_refs"]):
        raise ContractError("next_step references an absent answer ID")
    doorway = output.get("doorway")
    if not isinstance(doorway, dict) or not isinstance(doorway.get("status"), str) or doorway.get("status") not in {
        "recommended", "insufficient_evidence", "not_needed"
    }:
        raise ContractError("invalid doorway status")
    if doorway["status"] == "recommended":
        stage_id = doorway.get("stage_id")
        if not isinstance(stage_id, str) or stage_id not in DOORWAYS:
            raise ContractError("recommended doorway must use a registered stage_id")
        title, url = DOORWAYS[stage_id]
        if doorway.get("title") != title or doorway.get("url") != url:
            raise ContractError("doorway title and URL must exactly match the canonical registry")
        if not isinstance(doorway.get("rationale"), str) or not doorway["rationale"].strip():
            raise ContractError("recommended doorway requires a rationale")
    else:
        if any(doorway.get(k) is not None for k in ("stage_id", "title", "url")):
            raise ContractError("non-recommended doorway must not contain a destination")
    return output
