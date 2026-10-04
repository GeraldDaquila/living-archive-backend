# USE System Logic Audit — v487.96

## Purpose

Stabilize USE before adding further specialist capabilities.

## Current live baseline

- Runtime identity: v487.88
- Routing cleanup commit: 39e9d9b69eacfb561349f129af59aa823bf1cdd3
- Protected core: main_v487_28_runtime.py
- Protected core blob SHA: fb3208a8d287f16562ffd640d89f65d5e8d18607

## Audit findings

### 1. Request boundary
Resolved in v487.96. There is now one authoritative ASGI request boundary for POST /api/query and /. Superseded v487.56 middleware and v487.57 ASGI boundary were removed.

### 2. Guide capability routing
One active _guide_capability_route remains, but it still contains historical v487.72 provider/model arbitration and its own deterministic fallback. This is a distinct authority from the protected core's model-routing machinery and should be simplified into one routing arbitration contract.

### 3. Core mutation from main.py
main.py currently mutates protected core behavior by assigning:
- use_core._normalize_query
- use_core._weighted_inquiry_profile
- use_core._role_evidence
- use_core._unified_visitor_construction
- use_core.fetch_canonical_context

These are high-risk ownership crossings. The next cleanup phase should eliminate unnecessary monkey-patching and leave explicit adapters at the boundary instead.

### 4. Recommendation authority
Recommendation construction, outward evidence sanitation, canonical doorway selection, and evidence-bridging logic are implemented in main.py while the protected core already contains recommendation and canonical-selection mechanisms. This creates two generations of authority. The target state is one canonical owner for visitor construction and one explicit extension point for specialist closure gifts.

### 5. Relational closure
Completed HRN journeys currently invoke canonical retrieval directly from main.py and can perform a bounded second retrieval against a synthesized fallback query. This is valid behaviorally but is a second retrieval authority outside the normal request path. The target state is one closure contribution envelope handed to one canonical doorway-selection service.

### 6. Specialist boundary
The registry and adapters are comparatively clean. Planned capabilities are not invokable. Relationship and Formation are available. However main.py still assembles specialist context, transport metadata, response integration, and closure handling. Future specialists should enter through a single common contribution contract.

### 7. Version baggage
main.py contains active references from v487.45 through v487.94 despite runtime identity being v487.88. These should be treated as historical implementation lineage, not separate active authorities. Version-era code may remain only where its behavior is explicitly required by the current contract.

### 8. Observability
The service starts successfully and reports v487.88 identity, but the log stream is dominated by historical component labels. Observability should eventually report current ownership and contract boundaries rather than implementation history.

## Stabilization target

The desired architecture is:

request
→ one Guide interpretation/routing authority
→ one registry authorization gate
→ one specialist handoff seam OR protected core
→ one evidence/retrieval authority
→ one synthesis/generation authority
→ one visitor response boundary

For completed specialist journeys:

specialist
→ one normalized closure contribution
→ Guide-owned canonical doorway service
→ visitor-facing return

## Guardrails

- Do not modify main_v487_28_runtime.py.
- Do not change canonical embedding configuration.
- Do not introduce additional specialist integrations during stabilization.
- Prefer full-file replacements for code changes.
- Every cleanup commit must preserve protected hashes and pass startup/static invariants.
