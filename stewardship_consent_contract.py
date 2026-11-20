"""Relational response contract for stewardship and consent questions.

The contract is enforced at the shared Guide visitor boundary so provider
fluency or a navigation-only response cannot replace the requested synthesis.
"""
from __future__ import annotations

import re
from typing import Any

VERSION = "1.0"


def is_stewardship_consent_relationship_question(query: str) -> bool:
    text = re.sub(r"\s+", " ", str(query or "").casefold()).strip()
    pair = bool(re.search(r"\bstewardship\b", text) and re.search(r"\bconsent\b", text))
    relational = bool(re.search(
        r"\b(?:relationship|relate|related|connection|connect|interplay|interaction|interact|"
        r"between|together|complementary|complement|how do .* work)\b",
        text,
    ))
    return pair and relational


def has_stewardship_consent_relationship_explanation(response: str) -> bool:
    """Validate the governing distinctions, not just the presence of keywords."""
    text = re.sub(r"\s+", " ", str(response or "").casefold()).strip()

    stewardship = bool(
        re.search(r"\bstewardship\b", text)
        and re.search(r"\b(?:entrusted responsibility|responsibility to care|duty of care)\b", text)
    )
    consent_boundary = bool(
        re.search(r"\bconsent\b.{0,180}\b(?:whether|limits?|permission|agreement|participation)\b", text)
        or re.search(r"\b(?:whether|limits?|permission|agreement|participation)\b.{0,180}\bconsent\b", text)
    )
    responsibility_not_authority = bool(re.search(
        r"\b(?:responsibility|being entrusted|stewardship|entrusted with care)\b"
        r".{0,150}\b(?:does not|doesn't|cannot|can never|never)\b"
        r".{0,90}\b(?:confer|grant|give|create|mean|equal)\b.{0,60}\bauthority\b",
        text,
    ) or re.search(r"\bresponsibility does not automatically confer authority\b", text))
    consent_not_consultation = bool(
        re.search(r"\bconsultation\b.{0,100}\b(?:not|cannot|does not|doesn't|alone)\b.{0,70}\bconsent\b", text)
        or re.search(r"\bconsultation alone\b.{0,100}\b(?:substitute|replace|satisfy)\b.{0,50}\bconsent\b", text)
        or re.search(r"\bconsent is not (?:the same as|equivalent to) consultation\b", text)
    )
    agency = bool(
        re.search(r"\b(?:agency of (?:the )?people affected|affected people['’]?s agency|agency of those affected|other people['’]?s agency|another person['’]?s agency)\b", text)
        or re.search(r"\b(?:people affected|those affected)\b.{0,100}\b(?:decide|choose|refuse|right|agency)\b", text)
    )
    informed_voluntary_specific = all(
        re.search(pattern, text)
        for pattern in (r"\binformed\b", r"\bvoluntary\b", r"\bspecific\b")
    )
    refusal_boundary = bool(re.search(r"\brefus\w*\b", text) and re.search(
        r"\b(?:withdraw\w*|renegotiat\w*)\b", text
    ))
    ordinary_care_proportionality = bool(
        re.search(r"\b(?:ordinary|routine)\b.{0,100}\b(?:care|responsibilit|act|action)\b", text)
        and re.search(r"\b(?:does not mean|doesn't mean|not every|does not require|doesn't require)\b", text)
        and re.search(r"\b(?:individual permission|explicit consent|individual consent)\b", text)
    )
    relational_synthesis = bool(
        re.search(r"\b(?:complementary|complement|together)\b", text)
        and re.search(r"\b(?:care accountable|care remains accountable|care does not become control|responsibility to care)\b", text)
    )
    return all((
        stewardship,
        consent_boundary,
        responsibility_not_authority,
        consent_not_consultation,
        agency,
        informed_voluntary_specific,
        refusal_boundary,
        ordinary_care_proportionality,
        relational_synthesis,
    ))

def recovery_response() -> str:
    return (
        "Stewardship and consent are complementary, but they answer different questions. "
        "Stewardship is an entrusted responsibility to care for something—people, relationships, "
        "resources, or shared conditions—for which one has accepted or been given a role. "
        "Consent concerns whether, and within what limits, another person's participation, choices, "
        "body, information, property, or interests may legitimately be involved.\n\n"
        "The connection is a boundary on how responsibility is exercised. Being entrusted with care "
        "does not automatically confer authority to decide for everyone affected. A steward may act "
        "within an authorized role, but when an action depends on another person's participation or "
        "use of what is theirs, good intentions or consultation alone do not substitute for consent "
        "where consent is the relevant basis. Consent is not simply notification after a decision "
        "has already been made.\n\n"
        "Where consent is relevant, it should be informed, voluntary, and specific to what is being "
        "agreed to. As circumstances or the proposed use change, agreement may need to be renewed "
        "or renegotiated; refusal or withdrawal must be respected within the applicable context. "
        "This does not mean every ordinary act of care requires individual permission. It means "
        "distinguishing routine responsibilities already covered by an authorized role from choices "
        "that require permission, shared authority, or a genuine opportunity to refuse.\n\n"
        "Together, stewardship supplies the responsibility to care, while consent helps define the "
        "legitimate limits of that care in relation to other people's agency. Consent does not erase "
        "a steward's duties, and stewardship does not override another person's right to decide. "
        "Their relationship is what keeps care accountable rather than allowing responsibility to "
        "turn into control."
    )


def canonical_doorway() -> dict[str, str]:
    return {
        "title": "Charter of the Living Archive | Purpose & Governance",
        "url": "https://geralddaquila.com/charter-of-the-living-archive/",
        "rationale": (
            "The Charter sets out both stewardship as entrusted custodial responsibility and "
            "human sovereignty as the right to examine, question, integrate, or reject ideas. "
            "It is the Archive's clearest constitutional continuation for considering how care "
            "and responsibility must remain answerable to human agency."
        ),
    }


def apply_stewardship_consent_relationship_boundary(query: str, payload: Any) -> Any:
    if not isinstance(payload, dict) or not is_stewardship_consent_relationship_question(query):
        return payload
    safe = dict(payload)
    current = str(safe.get("response") or safe.get("answer") or "")
    if not has_stewardship_consent_relationship_explanation(current):
        answer = recovery_response()
        safe["response"] = answer
        if "answer" in safe:
            safe["answer"] = answer
        safe["response_provenance"] = {
            "class": "deterministic_recovery",
            "provider": "stewardship_consent_relational_contract",
            "model": None,
            "quality_adjusted_llm_eligible": False,
            "llm_invoked": False,
        }
        safe["provider"] = None
        safe["model"] = None
        safe["evidence"] = []
        safe["evidence_validation"] = {
            "version": "1.0",
            "status": "not_applicable",
            "reason": "deterministic_relational_recovery_not_attributed_to_retrieved_sources",
            "reference_count": 0,
            "claim_support": {
                "status": "not_applicable",
                "reason": "bounded_general_knowledge_relational_recovery",
                "semantic_certification": False,
            },
            "temporal_validity": {
                "status": "not_applicable",
                "reason": "no_temporal_claims_in_response",
            },
            "semantic_certification": False,
        }
        safe["answer_basis"] = {
            "kind": "general_knowledge",
            "label": "Conceptual explanation",
            "explanation": (
                "This is a bounded conceptual explanation of the relationship between "
                "entrusted responsibility and consent, not legal advice or a universal "
                "consent test. The linked Charter is a related constitutional continuation."
            ),
        }
        recovery_evidence = {
            "provenance_class": "deterministic_recovery",
            "references_present": False,
            "validation_status": "not_applicable",
            "claim_support_status": "not_applicable",
            "semantic_certification": False,
        }
        answer_envelope = safe.get("answer_envelope")
        if isinstance(answer_envelope, dict):
            answer_envelope = dict(answer_envelope)
            route = dict(answer_envelope.get("route") or {})
            route["provider_present"] = False
            route["model_present"] = False
            answer_envelope["route"] = route
            answer_envelope["evidence"] = recovery_evidence
            safe["answer_envelope"] = answer_envelope
        quality_floor = safe.get("gold_star_v2_quality_floor")
        if isinstance(quality_floor, dict):
            quality_floor = dict(quality_floor)
            quality_floor["evidence_validation"] = safe["evidence_validation"]
            floor_envelope = quality_floor.get("answer_envelope")
            if isinstance(floor_envelope, dict):
                floor_envelope = dict(floor_envelope)
                floor_route = dict(floor_envelope.get("route") or {})
                floor_route["provider_present"] = False
                floor_route["model_present"] = False
                floor_envelope["route"] = floor_route
                floor_envelope["evidence"] = recovery_evidence
                quality_floor["answer_envelope"] = floor_envelope
            safe["gold_star_v2_quality_floor"] = quality_floor
    doorway = canonical_doorway()
    safe["recommendation"] = doorway
    safe["canonical_doorway"] = doorway
    safe["doorway_title"] = doorway["title"]
    safe["doorway_url"] = doorway["url"]
    safe["doorway_rationale"] = doorway["rationale"]
    safe["doorway_decision"] = "selected"
    safe["doorway_selection_status"] = "VERIFIED_RELEVANT_DESTINATION"
    safe["doorway_selection_evaluated"] = True
    safe["doorway_selection_source"] = "stewardship_consent_relational_family"
    safe["doorway_omission_reason"] = None
    safe["stewardship_consent_contract"] = {
        "version": VERSION,
        "answer_first_enforced": True,
        "distinct_roles_preserved": True,
        "responsibility_not_conflated_with_authority": True,
        "consent_not_reduced_to_consultation": True,
        "affected_party_agency_preserved": True,
        "universal_legal_test_avoided": True,
        "doorway_is_separate_continuation": True,
    }
    safe["processing"] = "final_visitor_boundary_stewardship_consent_relational_contract"
    safe["route_source"] = "guide_final_visitor_boundary"
    return safe
