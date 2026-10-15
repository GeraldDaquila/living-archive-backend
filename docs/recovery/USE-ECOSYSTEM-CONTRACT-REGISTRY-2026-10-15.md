# USE Ecosystem Contract Registry — Recovery Draft

**Status:** Recovery design draft; documentation only; not yet an implemented runtime contract.  
**Created:** 2026-10-15  
**Purpose:** Consolidate fragmented system knowledge into a single auditable map without replacing live behavior or inventing missing source artifacts.

## 1. Operating invariants

1. The frozen General Purpose USE response is the gold-standard acceptance fixture. Do not redefine it during ecosystem integration.
2. `use_core.py` is protected. This document does not authorize changes to it.
3. The Guide is the visitor-facing USE orientation and navigation layer. It must answer the visitor usefully before offering an independently selected canonical destination when the request calls for explanation plus navigation.
4. Specialist adapters may route and normalize envelopes, but must not flatten, rewrite, or impersonate specialist voice.
5. HRN remains structurally isolated: Open Canvas → Living Fractal → Synthesis → Movement → Perspective Delta. Voice remains humane, empathetic, restrained, concrete, non-diagnostic, and non-prescriptive.
6. Catalogue responses must preserve canonical asset identity and URL. Never synthesize a URL or substitute an asset solely to fill a count.
7. If evidence is insufficient, return an honest bounded response or ask a clarifying question. Do not pad with irrelevant destinations.
8. WordPress administration uses Cowboy MCP only. WPVibe is retired.
9. Every recovered artifact needs source, retrieval time, byte size, hash, version, and confidence/provenance recorded before it can become authoritative.
10. Production release is NO-GO while a blocking subject-relevance or HRN composition defect remains open.

## 2. Verified deployment map at time of drafting

| Role | Service | Current evidence |
|---|---|---|
| Primary USE | `https://living-archive-backend.onrender.com` | Render service `srv-da98sm2jnfac73d2ki5g`, workspace `tea-da80ooqjnfac739kt5bg`, branch `main`; Guide E2E last recorded passing at v489.259 |
| USE mirror / backup | `https://living-archive-backend-mirror.onrender.com` | Render service `srv-db2s2bid0e5s73e7gt9g`, workspace `tea-db2s180m7kps73c3qa2g`, branch `main`; Guide E2E last recorded passing at v489.259 |
| Catalogue | `https://mini-use-payhip.onrender.com` | Render service `srv-dami28f40ujc73b15ej0`, workspace `tea-damhgg2d0e5s73ffis1g`, branch `main`; M0.15.70, 565 unique assets and 48 canonical cases in latest recorded E2E |
| Suspended QA services | `living-archive-v340-qa`, `living-archive-v334-lean-control` | Suspended in Render; preserve inventory, do not revive or delete without a specific need |
| Additional Catalogue-related services | `mini-use-payhip-m01554-candidate`, `mini-use-payhip-stewardship` | Active; dependency/caller trace required before any retirement |
| Additional backend service | `living-archive-backend-deuu` | Suspended; not the current mirror endpoint |

**Caution:** Versions above are the last recorded evidence available to this recovery effort, not a claim that every endpoint has been freshly queried during this documentation commit.

## 3. Proposed common response envelope (target contract, not yet implemented)

Adapters should normalize metadata without changing the specialist's authored content.

```json
{
  "contract": "use-response-v1",
  "request_id": "opaque-correlation-id",
  "producer": {
    "system": "guide-or-specialist-id",
    "version": "version-string",
    "fingerprint": "build-fingerprint"
  },
  "status": "ok",
  "response": "visitor-facing prose",
  "question": null,
  "recommendations": [
    {
      "asset_id": "canonical-id",
      "title": "canonical title",
      "url": "verified canonical URL",
      "role": "next-reading",
      "evidence": "brief evidence/rationale",
      "provenance": "catalogue or canonical retrieval source"
    }
  ],
  "diagnostics": {
    "fallback_used": false,
    "evidence_sufficient": true
  },
  "error": null
}
```

### Envelope rules
- `request_id` is opaque and propagated across Guide → specialist adapter → Catalogue/asset selection → WordPress bridge.
- Do not log visitor message, relationship details, or full generated prose merely to correlate a request. Use IDs, bounded reason codes, durations, versions, and counts.
- `response` is specialist-owned prose. Adapters may validate shape, not rewrite voice.
- `question` is nullable. For HRN, a missing question is a composition defect only where the turn contract requires one; a safe, local, visitor-grounded completion may be used only after its validators pass.
- `recommendations` must be empty or contain only canonical assets actually retrieved/verified. No fabricated IDs or URLs.
- `status` should distinguish successful response, bounded insufficient evidence, invalid request, and retryable operation failure. Exact enum values require implementation review.
- `producer.version` and fingerprint are required for live parity and regression attribution.
- Never expose internal stack traces, credentials, provider keys, or private diagnostics to visitors.

## 4. System boundaries

### The Guide / General Purpose USE
Owns orientation, intent interpretation, retrieval strategy, evidence-grounded explanation, and independent canonical navigation. The gold-standard composition remains the acceptance fixture. The Guide may hand off to a specialist, but it must not convert every explanatory question into a direct page handoff.

### Specialist adapters
Own routing and contract compatibility, not specialist reasoning or voice. Preserve explicit specialist IDs and versioned adapter contracts. Unknown or incompatible contracts must fail boundedly, not silently reinterpret data.

### Human Relational Navigator (HRN)
Owns relational inquiry and its distinct conversational progression. It is not a diagnostic, therapeutic, adjudicative, or prescriptive engine. The open defect is a live round-composition failure (`missing_question`); exact live v0.5.330 source is required before code repair. The tracked v0.5.326 and archived v0.5.310 sources are not substitutes.

### Living Archive Navigator (LAN)
Owns its own visitor navigation flow and corpus/index. The live subject-fit defect is reproduced. Exact live plugin source and authoritative corpus/index/build inputs are required before recovery or reconstruction. The current relationships export says unavailable; do not infer or fabricate relationships.

### Mini-USE Catalogue
Owns canonical asset identity, case/asset mapping, and verified destination URLs. Latest recorded baseline: M0.15.70, 565 unique asset IDs/URLs, 48 canonical cases. It must not silently compensate for missing LAN evidence with unrelated Catalogue assets.

### WordPress bridge
Owns transport between public WordPress UI and backend endpoints. Cowboy MCP is the only administrative channel. Bridge tests must check HTTP status, content type, contract version, response envelope, canonical URL integrity, and bounded error behavior.

## 5. Current blocking defects and recovery inputs

### LAN subject relevance
Reproduced query: “Where can I find material about institutional responsibility?” returned unrelated destinations (“How Do I Know What I Really Want?”, “Reference & Notes”, “GESARA Nodes”). Root cause indicated by live-source review: broad lexical scoring can pass without a hard final subject-fit gate; deterministic fallback can pad to three candidates.

**Required repair:** subject focus extraction from visitor wording; direct subject-evidence gate across retrieval, model plan validation, repair, and deterministic fallback; no irrelevant padding; humane clarification/insufficient-evidence response when fewer than three relevant canonical destinations qualify.

**Required source inputs:** exact live plugin source; `corpus-runtime.json`; `retrieval-index.json`; generator/build inputs; verifiable relationship export if one exists. The existing recovery PR #637 is a source snapshot only and is not deployable.

### HRN missing-question composition
Live v0.5.330 request about two colleagues disagreeing over responsibility-sharing returned HTTP 503 after four provider calls. Logs recorded `missing_question` and a rejected repair retry.

**Required repair:** trace the question field from REST input through composition and recovery; reproduce the empty-question/valid-prose state in tests; complete a single concrete, non-prescriptive, semantically aligned question locally only when safe; preserve HRN voice and do not log private conversation text.

**Required source input:** exact live v0.5.330 source via supported bounded-read/export. Do not restore v0.5.310 or overwrite with tracked v0.5.326.

## 6. Required regression fixtures

1. **General Purpose gold standard:** exact frozen composition and independently selected recommendation; preserve paragraph structure, voice, and complete response envelope.
2. **Guide explanatory routing:** “What is stewardship and why does it matter now more than ever?” must receive a useful explanation and a separate recommendation rather than a bare direct handoff.
3. **LAN subject relevance:** “Where can I find material about institutional responsibility?” must not return unrelated destinations; if evidence is insufficient, ask a grounded clarification.
4. **HRN composition:** “Two colleagues disagree about how responsibility should be shared. I want to understand the relationship without deciding who is right.” Valid grounded prose with an empty question must not cause a provider retry storm or generic fallback.
5. **Catalogue integrity:** 565 unique asset IDs and URLs; canonical cases/asset links remain valid; no synthetic destinations.
6. **Cross-service handoff:** one correlation ID across each available hop; contract mismatch and timeout are explicit, bounded failures.
7. **Privacy:** logs contain bounded reason codes, versions, timing, and request IDs, not private visitor content or secrets.

## 7. Release and rollback gates

- [ ] Exact source and recovery inputs identified; provenance and hashes recorded.
- [ ] Unit and contract tests pass, including empty-evidence, malformed-envelope, and timeout cases.
- [ ] All regression fixtures above pass.
- [ ] Live primary and mirror report expected versions/fingerprints and pass E2E.
- [ ] WordPress bridge and Catalogue handoff pass E2E with canonical URLs.
- [ ] Provider retry budget is bounded; no uncontrolled duplicate calls.
- [ ] Rollback target is the verified immediately prior production version, not an arbitrary older backup.
- [ ] Deploy primary and mirror only after all relevant gates pass; smoke-test both afterward.
- [ ] Keep release NO-GO while LAN or HRN blocking defects remain.

## 8. Evidence register

- Guide dual-service E2E: https://github.com/GeraldDaquila/living-archive-backend/actions/runs/38645881872
- LAN source snapshot / non-deployable recovery PR: https://github.com/GeraldDaquila/living-archive-backend/pull/637
- HRN live composition diagnosis: https://github.com/GeraldDaquila/living-archive-backend/issues/534
- Ecosystem recovery coordination issue: https://github.com/GeraldDaquila/living-archive-backend/issues/638

## 9. Change control

This document is a proposed integration contract, not authorization to change runtime behavior. Runtime adoption requires a separately reviewed implementation, full-file replacements where required, sequential commits, passing tests, explicit version advancement, and primary/mirror deployment only after QA. Keep the current production baseline intact while source recovery is incomplete.
