"""Architecture matrix for deciding what belongs in shared intelligence."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityDecision:
    name: str
    shared: bool
    rationale: str


DECISIONS = (
    CapabilityDecision("inquiry_or_movement_understanding", True, "Common prerequisite for routing and response construction."),
    CapabilityDecision("evidence_normalization", True, "Prevents cross-source fragments from being presented as one unsupported claim."),
    CapabilityDecision("claim_separation", True, "Useful for both factual and relational reasoning."),
    CapabilityDecision("synthesis", True, "Both general inquiry and specialist contributions require coherent integration."),
    CapabilityDecision("epistemic_boundaries", True, "Common protection against presenting interpretation as established fact."),
    CapabilityDecision("visitor_language_realization", True, "A site-wide visitor experience cannot depend on machine-shaped internal output."),
    CapabilityDecision("canonical_doorway_proposal", True, "Shared navigation primitive; USE retains final authority."),
    CapabilityDecision("provider_arbitration", True, "Potential platform primitive, pending comparison with HRN's live arbitration behavior."),
    CapabilityDecision("relational_conversation_state", False, "Distinctive HRN operating capability."),
    CapabilityDecision("perspective_delta", False, "Distinctive HRN outcome and steering mechanism."),
    CapabilityDecision("systems_diagnostic_logic", False, "Distinctive FSD operating capability."),
    CapabilityDecision("macro_specialist_routing", False, "USE owns orchestration and routing authority."),
)
