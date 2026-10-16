# USE Ecosystem Contract Registry v1

**Status:** architecture inventory; documentation-only proposal  
**Basis:** source inspected from `main` at commit `6fb85fe3efa229cbe2aba03dab489d6069e6f8e0` (USE v489.268), plus Render service metadata checked 2026-10-16. This document records the source-visible architecture and known verification gaps. It does not certify every live visitor journey.

## 1. Authority and ownership

- **The Guide / USE** owns the visitor request, route decision, invocation timing, common contract validation, canonical doorway selection, and final presentation.
- **Specialists** own their bounded reasoning and contribution semantics. The Guide must not flatten or rewrite specialist-owned language/state.
- **WordPress** is the canonical authority for published navigation nodes and the HRN plugin. Cowboy MCP is the sole authorized WordPress administration path.
- **The Catalogue** owns its native catalogue search and presentation. The Guide passes the visitor's original query through a canonical doorway; it does not duplicate Catalogue retrieval/ranking.
- **Provider Bank** is the provider-selection and failover authority. Specialist/provider-gateway callers select a semantic operation, not an individual model or credential.
- **Protected invariant:** `use_core.py` and the frozen General Purpose composition gold standard remain unchanged by this integration work.

## 2. Contract inventory (source-verified)

| Boundary | Contract/version | Responsibility | Status visible in source |
|---|---|---|---|
| Guide → specialist capability registry | `SPECIALIST_PIPE_CONTRACT_VERSION = v1` | Defines capability identity, public name, domain, purpose, entry point, trigger territory, access class, and declared status | Implemented in `specialist_registry.py` |
| Guide → hub request | `HUB_CONTRACT_VERSION = v1` | Carries request ID, Guide version, original question, recognized territory, processing purpose, Guide context, and safety state | Implemented in `hub_contracts.py` |
| Hub → specialist contribution | `HUB_CONTRACT_VERSION = v1` | Validates contract version, request ID, specialist ID, status, payload mapping, voice policy, and canonical candidates; preserves the full specialist payload | Implemented in `hub_contracts.py` and `boundary_resilience.py` |
| Guide adapter registry | `SPECIALIST_ADAPTER_CONTRACT_VERSION = v1` | Separates capability registration from an actual callable adapter; invocation does not itself decide routing, canonical resources, or visitor prose | Implemented in `specialist_adapters.py` |
| Seeing the Relationship / HRN contribution | `relationship-v2`; `preserve_specialist_voice` | Preserves HRN-owned human response, relational journey state, movement, and canonical-resource material | Adapter/validator implemented; exact live WordPress source and full live journey remain unverified |
| Stewardship Formation contribution | `formation-v1`; `preserve_specialist_boundary` | Returns bounded formation/navigation material, not a diagnosis and not automatically visitor-ready Guide prose | Adapter/validator implemented |
| Safety contribution | Safety adapter registered in runtime | Safety-oriented contribution and emergency-resource resolution | Adapter registered; test every safety/closure branch before release |
| Guide Node Registry | `GUIDE_NODE_REGISTRY_VERSION = v2`; schema v2 | WordPress-owned canonical navigation records; USE consumes validated records and decides whether to hand off | Runtime consumer present; live freshness/authority must be checked during E2E |
| General Guide composition | `general_guide_composition.CONTRACT_VERSION = v1.18` | Provider-neutral visitor-answer composition; generative calls cross Provider Bank | Source-present; frozen gold-standard regressions remain release gates |
| Provider gateway | `v1`; Provider Bank contract imported | Authenticated, provider-neutral semantic operations for HRN, Atlas, Mini-USE, and stewardship pathway | Source-present; configuration/readiness alone does not prove every operation succeeds |
| Guide SSE transport | `SSE-VALIDATED-v1`; transport `0.1.1` | Converts a completed Guide response to a validated SSE stream; does not generate content or alter specialist logic | Source-present; end-to-end proxy/transport checks still required |

## 3. Runtime adapter inventory versus declared capabilities

At the inspected `main.py` source, the runtime adapter registry explicitly registers:
- `relationship` → `RelationshipAdapter`
- `formation` → `FormationAdapter`
- `safety` → `SafetyUtilityAdapter`

The capability registry also contains planned entries for Catalogue, Philippine Systems Lens, and other bounded surfaces. A registry entry marked `planned` is not evidence of an invokable adapter.

**Catalogue is a deliberate separate doorway, not an omitted adapter by default.** The inspected Guide code has a dedicated Catalogue handoff that preserves the original query and returns a native Catalogue URL with `handoff_pending`, `return_mode=native_catalogue_search`, and a request ID. The Catalogue service owns search and presentation. Integration QA must test that the handoff opens the intended live Catalogue and retains the original query; it must not force Catalogue into the specialist-adapter registry without a separate architectural decision.

## 4. Required common trace and response semantics

For each visitor request, the integration test should correlate (without logging raw private visitor text):
1. A single request/correlation ID from the WordPress/Guide entry to the specialist call and final response.
2. Guide version and deployment fingerprint.
3. Selected route, route reason/class, and whether invocation was direct, delegated, or a native doorway.
4. Specialist ID and contract version; provider operation only when applicable.
5. Contribution status: `CONTRIBUTION`, `NO_CONTRIBUTION`, `DECLINED`, or `FAILED`.
6. Canonical candidate identity/title/URL and selection outcome, when resources are relevant.
7. Bounded failure/fallback provenance. A fallback must not impersonate a successful specialist composition.
8. Final WordPress rendering and, for HRN, return-to-Guide behavior without rewriting specialist-owned voice.

Common envelope checks must reject mismatched request IDs, specialist IDs, unsupported contract versions, invalid status values, and invalid payload types. Domain-specific validators remain responsible for specialist semantics.

## 5. Non-negotiable voice and safety boundaries

- HRN's public identity is **Human Relational Navigator / Seeing the Relationship**; tagline: “See the relationship before deciding what it means.”
- HRN's frozen writer and voice-policy methods are protected. The Guide and adapters must preserve HRN's language and journey state rather than substitute generic Guide prose.
- The Guide's General Purpose composition is the frozen gold-standard benchmark. No changes to `use_core.py` as part of integration repair.
- Safety interrupt, closure, and canonical-return branches take precedence over ordinary fallback.
- No unsupported resource, invented relationship, invented URL, or unverified source provenance may be introduced to make an integration appear complete.
- WordPress administration is exclusively through Cowboy MCP; WPVibe has been removed and must not be reintroduced.

## 6. Live blockers and release gate (checked 2026-10-16)

### HRN
The public HRN route returned HTTP 200 during a recent multi-turn check, but the journey was **not a pass**: turn 2 dropped supplied details into a generic opening, and turn 3 incorrectly changed “friend” to “partner” while turn position failed to advance monotonically. A separate recent resource-query sample showed machine-like reframing. These are semantic/voice defects, not UI styling defects.

Exact live HRN v0.5.330 source could not be retrieved through the current Cowboy file-reader path; tracked repository content at the expected HRN path is absent, and the older v0.5.326 or rollback v0.5.310 are not safe substitutes. The active WordPress HRN and composition guard directories exist, but source integrity/hash comparison is outstanding. Do not patch or deploy a guessed replacement.

### Render services
- Primary USE `srv-da98sm2jnfac73d2ki5g`: latest deployment LIVE at v489.268 / commit `6fb85fe3efa229cbe2aba03dab489d6069e6f8e0`.
- Canonical USE2-Mirror `srv-db2s2bid0e5s73e7gt9g`: service metadata confirms `suspended=not_suspended`; its latest deployment record is LIVE at the same commit as primary. Render app logs show `GET /` returning HTTP 200 at 2026-10-16 04:30 UTC and `/api/provider-capability` returning HTTP 200 at 04:21 UTC. These are endpoint-level smoke signals, not proof of a full visitor journey. Provider health-store timeouts and upstream rate-limit/timeout errors also appear in the same window.
- The redundant service `living-archive-backend-deuu` (ID `srv-db2scecs728c73ag0dn0`) was deleted on 2026-10-16 after confirming the canonical Mirror identity. It is no longer part of the active service inventory. The designated Mirror remains `srv-db2s2bid0e5s73e7gt9g`; do not recreate the redundant service.
- Catalogue `srv-dami28f40ujc73b15ej0`: latest deployment LIVE at M0.15.70 / commit `d2fd087cf7923fc02ddc108ed36fa01d6de5c42e`.
- Additional Catalogue workspace services (`mini-use-payhip-m01554-candidate` and `mini-use-payhip-stewardship`) remain present. Do not delete or suspend them until caller/dependency tracing proves it safe.

### Release decision
**NO-GO** until all relevant gates pass:
1. Exact HRN and guard source recovered through an authorized route; integrity hashes verified.
2. HRN frozen-writer invocation and voice-preservation branch proven.
3. Contract/unit tests pass for valid output, question-only recovery, monotonic turns, role fidelity, no false-success fallback, and safety/closure/canonical-return preservation.
4. Catalogue subject-fit and original-query doorway pass against the live service.
5. Public visitor journey, HRN return-to-Guide, and WordPress rendering pass on primary and canonical mirror.
6. Primary/mirror version and fingerprint parity plus health are verified after the mirror is resumed through Render's authorized control surface.
7. General Purpose gold-standard, Formation, safety, and Catalogue regression suites pass.

This file is a documentation-only contract map. It does not alter runtime behavior and does not authorize deployment.
