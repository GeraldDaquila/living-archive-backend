# Living Archive / USE Ecosystem Contract Registry

Status: **recovery draft — inventory only; not a production contract certification**  
Baseline inspected: `main` at `6fb85fe3efa229cbe2aba03dab489d6069e6f8e0` (USE v489.268, 2026-10-15).  
Master recovery record: [Issue #638](https://github.com/GeraldDaquila/living-archive-backend/issues/638). HRN voice/trace record: [Issue #669](https://github.com/GeraldDaquila/living-archive-backend/issues/669).

## 1. Invariants

- The Guide is the public face of USE: orient and navigate; do not silently turn every request into generic Q&A or a direct page handoff.
- General Purpose USE composition is a frozen acceptance benchmark. `use_core.py` is protected.
- HRN remains an isolated specialist. Preserve its humane voice and Open Canvas → Living Fractal → Synthesis → Movement → Perspective Delta architecture.
- Canonical assets, IDs, URLs, corpus relationships, and provider provenance must be evidence-backed. Missing evidence must not be fabricated.
- Cowboy MCP is the sole WordPress administration path. Do not introduce a second WordPress control plane.
- Primary and mirror are separate deployment targets and must each pass QA. A healthy `/health` response alone is not end-to-end proof.
- Do not overwrite live WordPress source with a repository snapshot until exact live-source provenance and a comparison are established.

## 2. Verified deployment inventory

| Component | Endpoint / identity | Evidence status | Open conflict / gap |
|---|---|---|---|
| USE primary | `https://living-archive-backend.onrender.com`; Render service `srv-da98sm2jnfac73d2ki5g`; repo `GeraldDaquila/living-archive-backend`, branch `main` | Render service metadata confirms active, free, auto-deploy from main. Repository main at inspected baseline declares v489.268. | Current runtime fingerprint and current health/route behavior must be freshly smoke-tested when a release is proposed. |
| USE mirror | `https://living-archive-backend-mirror.onrender.com`; Render service `srv-db2s2bid0e5s73e7gt9g`; same repository/branch | Render service metadata confirms active, free, auto-deploy from main. | Same commit does not prove equivalent environment variables or E2E behavior; parity needs live tests. |
| Mini-USE Catalogue | `https://mini-use-payhip.onrender.com` | Prior recovery record reports M0.15.70 E2E passed for 565 unique assets and 48 canonical cases. | Re-run live contract and handoff test before release; don't infer current deployment from historical pass. |
| Human Relational Navigator | WordPress plugin `plugins/human-relational-navigator/human-relational-navigator.php`, live version 0.5.330 | Cowboy MCP `wp_list_plugins` confirms active v0.5.330. | Exact live bytes/hash were not returned by the current Cowboy file-read call. Tracked repository file is v0.5.326 (blob SHA `eaa375da4d6d727b3eb778ae23c34efdc387f4b4`); old rollback artifact v0.5.310 is not an approved rollback. |
| HRN composition contract guard | `living-archive-hrn-composition-contract-guard`, v1.3.6 | Active plugin/version confirmed by Cowboy MCP. | Exact live source and whether it rewrites final prose are not yet established. |
| HRN command-boundary adapter | `hrn-command-boundary-adapter`, v1.3.0 | Active plugin/version confirmed by Cowboy MCP. | Exact live source and complete return-to-USE behavior are not yet established. |
| Provider Bank Bridge | `living-archive-provider-bank-bridge`, v0.2.1 | Active plugin/version confirmed by Cowboy MCP. | Provider routing/fallback trace across one request is still missing. |
| Provider Bridge Deadline Guard | `la-provider-bridge-deadline`, v1.2.0 | Active plugin/version confirmed by Cowboy MCP. | Live timeout/call-budget interaction with HRN has not been proven end-to-end. |
| Living Archive Navigator (LAN) | WordPress plugin `public-living-archive-navigator-v0.3.3-DUPLICATE-TITLE-GUARD-COLOR-NEUTRAL/living-archive-navigator.php`, plugin reports v0.3.3 | Active plugin/version confirmed by Cowboy MCP. | Known subject-relevance defect for “institutional responsibility”; authoritative live corpus/index and relationship export are missing. PR #637 is explicitly non-deployable until source artifacts are recovered. |
| Guide Node Registry | WordPress plugin `guide-node-registry/guide-node-registry.php`, v0.2.0-draft | Active plugin/version confirmed by Cowboy MCP. | Registry state must not be mistaken for proof that every registered capability is callable/live. Catalogue was previously reported as `planned` with auto-deploy disabled; reconcile this against live service before claiming integration. |
| Mini-USE WordPress adapter | `mini-use/mini-use.php`, v0.2.39 | Active plugin/version confirmed by Cowboy MCP. | Full visitor-path bridge and error-envelope compatibility still require current E2E evidence. |
| Emergency Intelligence | `living-archive-emergency-intelligence`, v0.1.2 | Active plugin/version confirmed by Cowboy MCP. | Invocation from relevant visitor journeys is unproven. |
| Living Glossary Intelligence | `living-glossary-intelligence`, v0.3.6 | Active plugin/version confirmed by Cowboy MCP. | Direct specialist invocation and return-envelope behavior are unproven. |
| Atlas Finder | `living-archive-atlas-finder`, v0.4.8 | Active plugin/version confirmed by Cowboy MCP. | Direct invocation and evidence/URL contract are unproven. |
| Stewardship Pathway Engine | `stewardship-pathway-engine`, v3.4.3 | Active plugin/version confirmed by Cowboy MCP. | Formation/Stewardship Institute path compatibility needs explicit contract tests. |
| Formation | WordPress entrance and Render backend/adapter described in recovery handoff | Prior handoff requires dedicated `POST /api/formation-entrance` contract then WordPress bridge → backend → FormationAdapter → contribution → bounded response. | Current exact route contract and live E2E result are not included in the verified evidence used for this draft. Treat as unverified, not absent. |

## 3. Common envelope — proposed compatibility checklist

This section is a **required contract checklist**, not a claim that every field is already implemented identically. Before an adapter is certified, document the exact wire names and test them.

- **Identity:** request/correlation ID preserved across Guide → specialist adapter → specialist → optional Catalogue/resource doorway → WordPress response.
- **Routing:** selected specialist, routing reason/category, and handoff status are explicit; no silent substitution with General Purpose output.
- **Content:** visitor-facing prose is distinct from metadata; specialist voice is preserved. Question/follow-up is optional and must be semantically aligned with the current turn.
- **Evidence/assets:** canonical title, URL, asset identifier, and provenance are explicit when present. Empty evidence is represented honestly; never pad with unrelated destinations.
- **Outcome:** success, bounded fallback, retryable provider failure, invalid contract, and insufficient evidence are distinguishable; HTTP status must agree with the body outcome.
- **Versioning:** producer version/fingerprint and adapter contract version are available for diagnostics.
- **Latency:** per-provider and whole-turn budgets are explicit; retries cannot exceed the caller's deadline.
- **Privacy:** logs contain IDs, branch/version, provider/model, elapsed time, and rejection category—not raw private visitor text or full generated prose.
- **Fallback semantics:** a recovery response must not claim to be frozen-writer output unless that writer actually produced and accepted it.

## 4. Blocking conflicts to resolve

1. **HRN source-of-truth conflict:** live plugin v0.5.330 vs tracked v0.5.326 vs old v0.5.310 rollback artifact. Recover exact live source, hash it, compare it; do not deploy either older file as a shortcut.
2. **HRN output provenance conflict:** screenshot contains abstract, consultant-like wording; production logs show missing-question/rejected repair paths, but no request correlation proving which branch supplied the screenshot response. Trace writer → validator → recovery → adapter → rendered response.
3. **Resource intent conflict:** “Where can I find material about institutional responsibility?” must remain a resource/navigation intent. HRN may retain its specialist voice, but the request must not be converted into a relational exercise. USE should return an evidence-backed canonical doorway in place.
4. **LAN evidence conflict:** subject-relevance defect is known, but authoritative live corpus/index/relationship inputs are unavailable in the recovery branch. Do not deploy PR #637 or invent corpus relationships.
5. **Registry/runtime conflict:** a registry entry or plugin being active is not proof the capability is callable, correctly routed, or E2E integrated. Reconcile declared state against actual route and visitor-path tests.
6. **Primary/mirror parity gap:** same repository/branch is not sufficient evidence. Compare live version/fingerprint, environment-dependent behavior, route outputs, timeout/fallback semantics, and visitor journeys independently.
7. **Formation contract gap:** establish and test `POST /api/formation-entrance` and the full WordPress → Render → FormationAdapter → contribution → bounded-response path before certifying Formation integration.

## 5. Required test matrix before release

| Case | Expected proof | Current status |
|---|---|---|
| General Purpose gold-standard question | Composition parity with frozen benchmark; no deterministic recovery masquerading as normal success | Blocking; provider-bank exhaustion previously observed |
| Institutional-responsibility resource query | Relevant canonical resource(s), correct title/URL, no irrelevant padding, no relational reframing | Blocking; LAN subject-fit defect reproduced historically |
| HRN friendship calibration | Humane concrete response; aligned follow-up; frozen writer provenance or explicitly identified bounded recovery | Blocking; screenshot is a negative fixture |
| HRN missing-question provider response | Local question completion only when grounded, concrete, non-prescriptive and aligned; otherwise safe failure | Blocking; prior repair retry rejected |
| HRN return-to-USE | Correlation ID preserved; canonical doorway returned and rendered in place | Unverified |
| Catalogue canonical asset | Stable canonical ID/title/URL and contract compatibility | Historical M0.15.70 E2E passed; current live replay required |
| Formation entrance | Exact POST contract and full visitor journey | Unverified |
| Emergency, Glossary, Atlas Finder, LAN, Stewardship Pathway | Real entry-point invocation and correct response contract, not just active plugin | Unverified |
| Primary and mirror | Same intended commit/version plus independent live route and visitor-path passes | Historical health checks are insufficient; current full parity unverified |

## 6. Release decision

**NO-GO while HRN source provenance, HRN voice/return path, and LAN subject relevance remain blocking.** Do not deploy this inventory document to production as a code change; it is documentation for review and subsequent executable contract tests. Update each status only with linked test output, exact commit/version, and timestamp.
