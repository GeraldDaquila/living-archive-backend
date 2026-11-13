# USE Live-State Reconciliation — 2026-10-15

**Scope:** Read-only production audit using Cowboy MCP outbound HTTP and Render inventory. No visitor model-backed query was sent during this check. No service or WordPress content was changed.

## 1. Fresh endpoint results

### Primary USE
- URL: `https://living-archive-backend.onrender.com/api/integration-audit`
- HTTP: 200
- Version: `v489.259`
- Fingerprint: `USE-v489.259-subject-discovery-quality`
- Build ID: `USE-BUILD-v489.259-subject-discovery-quality`
- Source SHA-256: `3aecd273fbde8ad1ab438472c406e6343c13e6e807eea204c6d7efb614ca6346`
- Response says the audit contract is `ecosystem-integration-audit-v1`.

### Mirror USE
- URL: `https://living-archive-backend-mirror.onrender.com/api/integration-audit`
- HTTP: 200
- Version, fingerprint, build ID, and source SHA-256 match the primary exactly.
- Both services have distinct boot IDs and request IDs, as expected for separate runtime instances.

### Catalogue
- URL: `https://mini-use-payhip.onrender.com/health`
- HTTP: 200
- Version: `M0.15.70`
- `catalogue_assets=565`
- `provider_independent=true`
- Exposes `/api/navigate` and `/api/case-search`.

## 2. What the live audit does and does not establish

The primary and mirror report the same capability registry:
- Relationship / “Seeing the Relationship”: available, public.
- Formation / “Stewardship Formation Navigator”: available, formation access.
- Safety / Crisis: available, safety access.
- Catalogue / “Stewardship Catalogue”: marked planned, catalogue access.
- Philippine Systems Lens: marked planned, public access.

Declared runtime adapters: `formation`, `relationship`, `safety`. The audit reports no available capabilities missing adapters and no adapters without capabilities. Catalogue is explicitly described as `direct_handoff_not_adapter`; its direct handoff is `native_catalogue_search`.

**Important:** The endpoint itself says it reports registration and declared routing mode only; it does not assert provider health or end-to-end visitor journey success. Therefore this is contract/identity evidence, not proof that every specialist works end to end.

## 3. Reconciliation decision

1. Primary and mirror are currently on the same verified release identity. Keep this parity as the baseline.
2. Do not treat the integration-audit capability registry as a complete list of all visitor-facing features. It is a registration snapshot with explicit limitations.
3. Treat Catalogue's `planned` registry status alongside a declared native direct handoff as a documentation/semantics question to reconcile. Do not change live routing merely to make labels consistent.
4. Continue to treat HRN's live question-composition defect and LAN's subject-relevance defect as release blockers.
5. The Guide's frozen General Purpose composition and protected `use_core.py` remain untouched.
6. No live model-backed E2E was repeated in this audit, to avoid unnecessary provider calls while HRN's failure mode is under investigation.

## 4. Next safe actions

- Recover exact LAN source plus authoritative corpus/index/build inputs from an authenticated downloadable backup; verify paths, sizes, hashes, and provenance before reconstructing.
- Recover exact live HRN v0.5.330 source through a supported export or bounded-read path. Do not substitute v0.5.326 tracked source or v0.5.310 rollback artifact.
- Prepare regression fixtures and a contract test matrix in the repository; run tests against recovered source before any runtime patch.
- After source repair and QA, run the existing dual-service Guide E2E plus explicit HRN return-to-Guide, LAN subject-fit, Catalogue canonical-link, Formation, safety boundary, timeout/fallback, and WordPress bridge journeys.
- Deploy primary and mirror only after the full relevant release gate passes.

## Evidence links
- Guide E2E: https://github.com/GeraldDaquila/living-archive-backend/actions/runs/38645881872
- Ecosystem recovery issue: https://github.com/GeraldDaquila/living-archive-backend/issues/638
- Contract registry PR: https://github.com/GeraldDaquila/living-archive-backend/pull/639
- LAN source snapshot PR: https://github.com/GeraldDaquila/living-archive-backend/pull/637
- HRN live composition blocker: https://github.com/GeraldDaquila/living-archive-backend/issues/534
