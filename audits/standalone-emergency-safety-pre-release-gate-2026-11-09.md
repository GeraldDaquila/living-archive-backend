# Standalone Emergency and Safety Pre-Release Gate
Date: 2026-11-09
Branch under review: `safety/standalone-deterministic-20261109`
Decision: **NO-GO — development architecture passes; release evidence remains incomplete.**

## Gate summary

| Gate | Status | Evidence | Release condition |
|---|---|---|---|
| HRN retirement from Guide safety path | PASS | Standalone state-machine tests; no-HRN snapshot | Keep archived HRN out of runtime path |
| Deterministic Safety | PASS | GitHub Actions #42607961197 | Preserve deterministic transitions |
| Authenticated continuity | PASS (development) | Signed-token round trip and tamper rejection | Provision production secret and rotation procedure |
| EI API boundary | PASS | Combined EI validation #42606912256 | Maintain strict no-visitor-content boundary |
| EI registry parity | BLOCKED | Five countries currently represented | Reach approved ten-country target |
| Resource source verification | BLOCKED | Schema/provenance checks only | Human verification against authoritative sources |
| Remote updates | PASS as fail-closed | Disabled security gate tested | Keep disabled until signed update protocol exists |
| Service arbitration | PARTIAL | Basic selector tests | Define taxonomy and country-specific arbitration tests |
| Safety content review | BLOCKED | Ported deterministic baseline only | Complete designated human safety review |
| Visitor-facing browser E2E | BLOCKED | No Guide browser staging run | Test only against isolated staging |

## Findings

### 1. The architecture is structurally ready for controlled staging
The Guide owns risk detection and deterministic conversation movement. EI owns resource resolution. EI rejects visitor messages and transcript-like fields at its REST boundary.

### 2. Continuity is no longer client-authorized
The current branch uses an HMAC-authenticated opaque token. It carries deterministic state, question, expiry, nonce and a one-way request hash. It does not carry visitor text. Tampered tokens are rejected by regression tests.

### 3. Registry expansion must not be rushed
Adding five countries merely to satisfy a numeric target would weaken the safety architecture. Each new country should enter through a verification record with an authoritative source, explicit scope, review date, and a country-specific test.

### 4. Browser E2E requires a real staging boundary
The current repository tests validate modules and disposable WordPress REST behavior. They do not demonstrate that the live Guide UI sends, preserves and consumes the authenticated safety-session token correctly. Production must not be used as the test target.

## Required closure sequence

1. Provision a dedicated isolated staging target or disposable Guide deployment with no production traffic or credentials.
2. Configure a staging-only `SAFETY_SESSION_SECRET`.
3. Run browser E2E for first disclosure, acute progression, emergency-resource presentation, token continuity, token tampering, recovery, release, location unknown and location refusal.
4. Complete human review of safety wording and transitions.
5. Expand EI only with independently verified records and corresponding tests.
6. Re-run the combined pre-release gate.
7. Require explicit release approval before merge or deployment.

## Infrastructure protection

Mini-USE Workspace remains inspection-only. No existing Render service is to be repurposed, reconfigured, or replaced for this gate. No new Render service is created by this review.

## Release decision

**NO-GO.** The remaining blockers are evidence and governance gates, not evidence of a broken standalone architecture. The correct next operational move is isolated staging design—not production testing and not further changes to existing Mini-USE infrastructure.
