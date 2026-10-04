# Legacy USE Harvest Matrix — Post-Oct. 1

## Scope

This document records the first harvest pass over the preserved pre-Oct. 1 USE lineage and identifies what should survive into the new-generation spoke-and-hub ecosystem.

The purpose is not to port the old implementation wholesale. It is to retain proven principles while leaving historical routing and prototype accumulation behind.

## Harvested practices

| Legacy practice | Harvest value | New-generation treatment |
|---|---|---|
| Evidence normalization | High | Shared hub primitive |
| Claim normalization with epistemic treatment | High | Shared hub primitive |
| Synthesis-material packaging | High | Shared hub service/contract |
| Bounded canonical doorway representation | High | Shared hub contribution contract |
| Journey contribution envelope | High | Common specialist closure contract |
| Specialist registry with planned/available separation | High | Hub capability registry |
| Adapter boundary between Guide and specialist | High | Standard spoke interface |
| Specialist contribution validation | High | Mandatory ingress/egress validation |
| Specialist-owned voice policy | High | Preserve as specialist contract |
| Provider credentials isolated from Guide | High | Specialist provider boundary |
| Bounded fallback behavior | Medium/High | Re-express as explicit service policy |
| Safety state carried as bounded context | High | Shared safety contract |
| Request-boundary consolidation | High | One hub request boundary |
| Historical deterministic inquiry heuristics | Low/conditional | Harvest concepts only when independently justified |
| USE-specific recommendation heuristics | Low/conditional | Do not inherit automatically |
| Main-to-core monkey patches | Negative as architecture | Retire from new-generation mainline |
| Duplicate retrieval/recommendation authority | Negative as architecture | Consolidate to one explicit owner |
| Historical version-era routing layers | Negative as architecture | Preserve only in legacy branch/reference history |

## Existing post-Oct. 1 assets already aligned

The preserved ecosystem already contains several reusable boundaries:

- `shared_intelligence_primitives.py` provides pure evidence, claim, synthesis, doorway, and journey primitives.
- `shared_evidence.py` adapts evidence normalization into the legacy dictionary shape.
- `specialist_registry.py` separates capability registration from runtime availability.
- `specialist_adapters.py` defines the Guide-to-specialist adapter seam.
- `relationship_contribution.py` protects specialist voice and structured relational contribution.
- `formation_contribution.py` provides a bounded Formation contribution grammar.
- `provider_gateway_contract.py` keeps specialist provider selection/transport outside the Guide.

These should be treated as the initial hub vocabulary rather than as reasons to keep the historical USE internals alive.

## Harvest principle

A legacy behavior is promoted only when its value can be stated independently of its old implementation.

Examples:

- "Normalize evidence before downstream reasoning" is promotable.
- "Call this particular USE helper before that historical helper" is not.
- "Keep provider selection outside the Guide" is promotable.
- "Preserve this v487.xx fallback branch" is legacy-specific unless its behavior proves independently necessary.

## Repurposing target for legacy USE

After the mainline harvest is complete, the legacy branch should become a bounded general-purpose utility capability.

Its job is to handle:
- questions outside specialist trigger territories,
- broad exploratory requests,
- compatibility cases,
- experimental workflows,
- and future capabilities awaiting specialistization.

It should be callable explicitly as a utility/fallback spoke or service. It must not become a hidden dependency of the specialist spokes.

## Next architectural task

The next code phase should establish a minimal hub contract for:
1. capability recognition,
2. specialist invocation,
3. normalized contribution,
4. shared canonical/navigation handling,
5. final visitor response.

Only after that contract is stable should historical USE internals be removed or retired from mainline execution.
