# System Invariant Lock — Living Archive

Status: proposed release-control contract, 2026-10-14. This document is not evidence that production controls are already active.

## Non-negotiable invariants

1. **Protected core:** use_core.py is immutable under ordinary feature work. Any attempted change must fail CI. A separate, explicitly authorized constitutional change process is required; do not bypass this check by force-pushing or merging around CI.
2. **Frozen WordPress theme:** Twenty Twenty-Five and its templates are not owned by this project and must not be edited. WordPress integration work must use owned plugin/snippet/page boundaries only.
3. **Frozen specialist voice:** HRN voice policy remains unchanged by integration, routing, provider, or UX repairs.
4. **Contract compatibility:** API, adapter, specialist, and handoff contracts are versioned. A change must include compatibility tests for producers and consumers; no silent shape changes.
5. **Evidence and safety boundaries:** Canonical links and claims must remain evidence-grounded. Emergency guidance must honor explicit location, refusal, conflicting evidence, and verified-resource selection rules.
6. **Sequential versioning and provenance:** Every release advances sequentially and records source commit, build identity, service, contract versions, and deployed fingerprint. A version string alone is not proof of provenance.
7. **No promotion on missing evidence:** A skipped, timed-out, unavailable, or absent check is UNVERIFIED, never PASS.
8. **Post-deploy verification:** A successful build/deploy is not an E2E pass. Verify actual live source identity and critical journeys on each production service.

## Required release gate

- [ ] Protected-file diff check passed; frozen theme not edited.
- [ ] Static checks and deterministic regression tests passed on the exact candidate commit.
- [ ] Contract/adapter registry and compatibility tests passed.
- [ ] Specialist multi-turn tests passed, including HRN synthesis/junction/resource gift and HRN → USE → Guide handoff.
- [ ] Mini-USE orientation, public-governance boundary, case discovery, navigation selection, systemic relation, semantic calibration, and presentation-boundary audits passed.
- [ ] Emergency resolver tests passed for missing location, explicit location, refusal, denied/unavailable browser location, conflicting evidence, and verified resource selection.
- [ ] Primary and Mirror source fingerprints and contract versions match the approved release.
- [ ] WordPress Guide integration tested end-to-end in a browser; API-only tests are not a substitute.
- [ ] Deploy only after every required gate is PASS. If any test is unavailable or times out, hold release, investigate with direct service checks, and rerun.
- [ ] After deploy, repeat health, fingerprint, regression, safety, and browser E2E checks; roll back on invariant failure.

## Change protocol

1. Identify the owning repository/component and authoritative live baseline.
2. Make the smallest structural change in a branch; never edit protected components as a shortcut.
3. Add a regression test that fails against the known defect.
4. Run tests on the exact commit and review CI results.
5. Promote only after all release-gate evidence is recorded.
6. Verify deployed commit/fingerprint and repeat critical E2E journeys on Primary and Mirror where applicable.

## Current known release blockers (2026-10-14)

- Mini-USE M0.15.70 still exhibits public-governance synthesis drift; proposed M0.15.71 repair is not yet proven by executed tests.
- HRN third-turn novelty/synthesis and specialist handoff remain unverified/failing calibration.
- Several Mini-USE audits and WordPress-proxied live checks timed out; these are not passes.
- Browser-level Guide E2E is not yet verified.
- Repository use_core.py reports v333 while the recorded production baseline is v489.233. Reconcile source provenance before asserting repository/deployment parity.

Until these blockers are closed, production release status is HOLD.
