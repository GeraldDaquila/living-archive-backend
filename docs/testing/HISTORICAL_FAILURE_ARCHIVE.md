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
| Current disposition | **Initial disposition: 24 SUPERSEDED, 4 REPAIR, and 84 UNRESOLVED.** The additional follow-up doorway expectation is tracked separately as repaired. See the per-test register. |

This is intentionally conservative. The aggregate count is a diagnostic lead, not sufficient evidence to archive individual tests. The GitHub Actions workflow added alongside this document reruns the full suite on the current branch and publishes a JUnit report plus a human-readable node-ID inventory. Each result must then be adjudicated against the current USE / The Guide contracts.

## Current testing hierarchy

1. **Active Contract Suite** — current architecture, visitor safety, privacy, access boundaries, Gold Star behavior, runtime reliability, and production-critical behavior. Blocking.
2. **Evolution / Regression Suite** — verifies that architectural improvements persist and resolved failure modes do not return. Blocking where the contract is current.
3. **Historical Diagnostic / Archive** — non-blocking inventory and explicitly retired tests. Its failures remain visible in reports but do not count as active-contract failures after documented retirement.

## Retirement gate

A retirement is complete only when the exact test node ID is recorded here with a supported disposition, its replacement/coverage implications are reviewed, the active suite still covers the current contract, and CI confirms the change. Until then, the test remains unresolved—not archived.

## Reproducible baseline execution

- Archive bootstrap commit: `ee2772e7154ae8a4b9557772e45283c8374dc41a`.
- The first post-bootstrap GitHub Actions run is the authoritative per-test inventory for the current mainline. It must be evaluated independently from the earlier aggregate snapshot above.
- The JUnit XML and generated Markdown inventory are retained as the `historical-test-failure-inventory` workflow artifact for 30 days. The exact workflow run, commit, counts, and artifact reference should be recorded here after completion.
- This diagnostic does not automatically retire tests. All findings begin as UNRESOLVED until reviewed against current contracts.

## First reproducible inventory and adjudication

| Field | Value |
|---|---|
| Workflow | [Historical test failure inventory](https://github.com/GeraldDaquila/living-archive-backend/actions/runs/44857281404) |
| Run ID | `44857281404` |
| Tested main commit | `ee2772e7154ae8a4b9557772e45283c8374dc41a` |
| Artifact | `historical-test-failure-inventory` (artifact ID `14688122820`) |
| Result | 2,358 test cases; 112 failures; 0 errors; 3 skipped |

### Confirmed superseded version-snapshot failures — 24

These tests asserted that the live `main.py` still contained exact implementation details, function names, deployment fingerprints, and protected-core hashes from USE v379–v386. The production runtime is now v489.315; these assertions cannot remain active against a later architecture. The original source files are preserved, uncollected, under `docs/testing/historical-test-snapshots/` with the `.py.archive` suffix.

| Original test file | Failed assertions retired |
|---|---:|
| `test_v374_visitor_experience_architecture.py` | 7 |
| `test_v381_transition_evidence_bridge.py` | 3 |
| `test_v382_transition_selection_continuation.py` | 3 |
| `test_v383_direct_transition_bridge.py` | 2 |
| `test_v384_visitor_authority.py` | 2 |
| `test_v385_open_transition_doorway_fit.py` | 2 |
| `test_v386_sensitive_guide_recovery.py` | 5 |
| **Total** | **24** |

Disposition: **SUPERSEDED**. Their source-snapshot assumptions are retired, not the underlying safety or visitor-experience requirements. Current contract coverage is maintained through the v489 relational-routing/return-evidence tests (`test_v489_85`, `test_v489_86`, `test_v489_89`), HRN movement/perception tests, and Gold Star v2 visitor-boundary/runtime-authority tests. The original files remain available for historical inspection.

### Confirmed repairs

`tests/test_v489_282_home_navigation_heading_boundary.py::test_explicit_living_archive_homepage_navigation_is_deterministic` expected the response version to remain hard-coded at `v489.282`. The test now compares against `main.APP_VERSION`, preserving the navigation contract while allowing sequential releases. Disposition: **REPAIR** (not retired).

### Remaining failures

The other **84 of the original 112** remain active and unresolved. They are not declared obsolete; they require individual contract-level review. In particular, failures involving current Gold Star authority/transfer, visitor doorway selection, subject grounding, provider budgets, safety boundaries, and HRN routing are treated as possible live contract regressions—not archived by age or label.

The latest inventory run below validates the retirement and repair changes. The per-test CSV register records the disposition of every baseline failure plus the one additional follow-up failure.


### Additional confirmed test-harness repairs

- `test_culture_doorway_contract.py`: injects the current `main._normalize_query` helper into its isolated execution namespace.
- `tests/test_care_commons_final_boundary.py`: targets the current shared `_guide_finalize_visitor_payload` boundary rather than a removed helper.
- `tests/test_general_guide_conceptual_relationship.py::test_algorithmic_amplification_contract_names_mechanism_before_system_context`: imports the missing `Path` dependency.
- The follow-up doorway test now permits omission or a valid canonical destination, and rejects malformed/non-canonical navigation. The earlier test expected an unconditional absence even though the current canonical registry can supply the Applied Stewardship Toolkit.

## Latest current-suite result

| Field | Value |
|---|---|
| Workflow | [Historical test failure inventory run 44858288728](https://github.com/GeraldDaquila/living-archive-backend/actions/runs/44858288728) |
| Tested commit | `e90c565d530efd7aeaa8a444c080f375bae60cfb` |
| Artifact | `historical-test-failure-inventory` (artifact ID `14688094879`) |
| Test cases | 2,327 |
| Failures | **84** |
| Errors | 0 |
| Skipped | 3 |
| Workflow job | Success; pytest remains intentionally non-blocking so the complete failure inventory is always uploaded |

The 84 remaining failures are still visible in the report and remain **UNRESOLVED**. They include current Gold Star response/registry contracts, canonical evidence selection, visitor intent and doorway behavior, provider budgets, and HRN routing. They are not removed from the active suite.

The current PR head also passed the targeted Guide resource-discovery evidence workflow, provider-health regression, mocked-UI continuity contract, and the v487 production-validation workflow. These focused passes do not erase the 84 broader diagnostic failures.

The authoritative row-by-row record is `docs/testing/HISTORICAL_FAILURE_REGISTER.csv`: 24 SUPERSEDED, 5 REPAIR (including the follow-up discovery), and 84 UNRESOLVED.
