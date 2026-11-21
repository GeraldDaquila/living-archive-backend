# Historical Test Failure Archive

## Purpose

Preserve the evidence of earlier USE / The Guide implementations without allowing obsolete assertions to define the current system contract. This archive is a record of test retirement decisions, not a mechanism for concealing failures.

## Disposition rules

Every failure receives one of these dispositions:

- **ACTIVE** — still expresses a valid current safety, privacy, access, reliability, or product-behavior contract. Keep in the blocking suite.
- **REPAIR** — the intended contract remains valid but the test, fixture, mock, schema, or setup is broken. Fix the test or implementation; do not retire it.
- **SUPERSEDED** — a documented newer architecture or contract replaces the old expectation. Retire the obsolete assertion only after its replacement is identified or explicitly documented as unnecessary.
- **IRRELEVANT** — no longer tests a responsibility of the current system. Retire with a reason and evidence.
- **UNRESOLVED** — evidence is insufficient to determine whether the failure is obsolete or a real regression. Keep visible and investigate; never silently suppress it.

A failure is not historical merely because it is old, flaky, inconvenient, or currently failing. No test is deleted solely to improve the pass rate.

## Required record for each retired test

Record the exact test node ID, previous failure signature, disposition, rationale, superseding architecture/contract, replacement test (if any), source diagnostic run and commit, and retirement commit/date. Preserve original test source in Git history. Where feasible, move retired assertions into a non-default historical test area rather than deleting their provenance.

## Initial diagnostic snapshot

| Field | Value |
|---|---|
| Source PR | [#1839](https://github.com/GeraldDaquila/living-archive-backend/pull/1839) |
| Diagnostic commit | `7ca72fdf3c5e882ad324db43bf95121c3830c8e0` |
| Reported result | 2,237 passed; 112 failed; 3 skipped; 264 subtests passed |
| Scope note | The PR reported the failures as legacy/version-pinned Guide/HRN assertions outside the new claim-adjudication contract. |
| Evidence limitation | The aggregate result did not include a verified per-test failure inventory or a clean baseline comparison proving all 112 failures pre-existed. |
| Current disposition | **112 UNRESOLVED — inventory required; zero tests authorized for retirement on this aggregate evidence alone.** |

This is intentionally conservative. The aggregate count is a diagnostic lead, not sufficient evidence to archive individual tests. The GitHub Actions workflow added alongside this document reruns the full suite on the current branch and publishes a JUnit report plus a human-readable node-ID inventory. Each result must then be adjudicated against the current USE / The Guide contracts.

## Current testing hierarchy

1. **Active Contract Suite** — current architecture, visitor safety, privacy, access boundaries, Gold Star behavior, runtime reliability, and production-critical behavior. Blocking.
2. **Evolution / Regression Suite** — verifies that architectural improvements persist and resolved failure modes do not return. Blocking where the contract is current.
3. **Historical Diagnostic / Archive** — non-blocking inventory and explicitly retired tests. Its failures remain visible in reports but do not count as active-contract failures after documented retirement.

## Retirement gate

A retirement is complete only when the exact test node ID is recorded here with a supported disposition, its replacement/coverage implications are reviewed, the active suite still covers the current contract, and CI confirms the change. Until then, the test remains unresolved—not archived.
