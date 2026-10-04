# New-Generation Architecture — Post-Oct. 1

## Architectural decision

The pre-Oct. 1 USE implementation is preserved as a legacy/general-purpose learning branch. It is not the governing architectural authority for the post-Oct. 1 ecosystem.

Legacy preservation branch: `legacy/use-pre-oct-1`

## Mainline principle

The main branch is the integration surface for the new-generation ecosystem.

Core direction:

request
→ Guide interpretation/orientation
→ specialist recognition
→ specialist execution
→ normalized contribution
→ shared synthesis/navigation
→ visitor response

The legacy USE stack may be harvested through explicit contracts, but its historical routing, deterministic prototype layers, monkey patches, recommendation heuristics, and fallback machinery must not become prerequisites for new specialists.

## Boundaries

### Legacy USE

Purpose:
- general-purpose fallback
- compatibility
- experimental/reference implementation
- harvesting of proven capabilities

Non-purpose:
- systemic authority over new specialists
- mandatory inheritance by HRN or later specialists

### New-generation specialists

Each specialist owns its domain intelligence and conversational behavior.

Each specialist enters the ecosystem through:
1. registry authorization
2. explicit adapter
3. specialist-owned execution
4. normalized contribution
5. shared downstream handling

Specialist voice remains specialist-owned.

### Guide

The Guide provides orientation, shared contracts, routing/recognition, and canonical navigation services.

It should not absorb specialist reasoning into historical USE logic.

### Retrieval and canonical navigation

There should be one explicit retrieval/navigation authority. Specialist closures provide normalized contributions rather than implementing independent canonical retrieval stacks.

## Cleanup rule

Before modifying historical USE machinery, determine whether the behavior is:
- required by the current mainline contract,
- harvestable as an explicit service,
- or legacy residue.

Legacy residue should be retired from the mainline rather than repeatedly patched.

## Protected core

The protected USE core remains immutable unless a separate architectural decision explicitly changes that protection.

## Operational implication

Future specialist integrations should be designed against the post-Oct. 1 contracts first. They should not be fitted into the historical USE stack merely because that stack already exists.
