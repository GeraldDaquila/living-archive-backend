# Standalone Emergency and Safety Architecture Audit
Date: 2026-11-09
Branch: `safety/standalone-deterministic-20261109`
Status: development validation passed; production release remains NO-GO.

## Architectural decision
HRN retirement is intentional. The Guide must not depend on the HRN WordPress endpoint for safety follow-up.

The standalone architecture is:
- **The Guide:** sitewide safety boundary, first-turn detection, and orchestration before ordinary Guide routing.
- **Standalone Safety state machine:** deterministic answer classification, state transitions, intervention sequence, and conversation continuity in `safety_intelligence.py`.
- **Emergency Intelligence (EI):** independent verified resource registry, location provenance, service selection, and presentation in the standalone WordPress plugin.
- **LLM:** may supplement first-turn safety-signal recall; it does not classify follow-up answers, select deterministic stages, or author/override the safety transition sequence.

## HRN dependency removed
The previous Python Safety utility called the HRN WordPress endpoint for follow-up safety turns. The first-turn path could respond locally, but subsequent turns still relied on HRN for answer classification, transitions, and intervention wording.

This branch:
- Removes `DEFAULT_HRN_ENDPOINT` and `_request_hrn_safety` from `safety_intelligence.py`.
- Ports the protected deterministic transition sequence into the local Python Safety state machine.
- Recovers the active stage from the preceding safety question and assistant movement, including repeated recovery questions.
- Requires a second explicit affirmative safety confirmation before release.
- Keeps emergency-resource lookup independent; EI failure does not suppress the deterministic safety message or next question.
- Changes the Guide startup invariant to require `hrn_dependency == false` and `standalone_safety_state_machine == true`.
- Removes HRN safety labels from the utility, adapter, Guide display mode, and safety logging.

The archived HRN plugin remains in the repository as source history. No HRN plugin file is modified by this branch, and the Guide safety path no longer calls its endpoint.

## EI resource authority
The EI plugin is maintained separately on `ei/standalone-provenance-20261109` and included unchanged in this branch:
- Version 0.1.3; registry schema 0.2.
- Strict local registry validation and stale-cache clearing.
- Resource-to-verification evidence mapping and freshness checks.
- Explicit user location outranks browser/IP/timezone/locale inference.
- Verified primary and secondary resource presentation.
- Remote registry updates fail closed; no network update request is made.
- Public REST input boundary rejects visitor messages, transcripts, unsupported fields, overlength location data, and unsupported service categories.

## Validation evidence
### EI branch
- GitHub Actions run #42606912256 on the combined Safety branch: success.
- PHP syntax, registry JSON, provenance/expiry, location precedence, resource alternatives, update security gate.
- Disposable WordPress + MariaDB bootstrap with EI plugin only.
- Real REST dispatch: PH 911, unknown location, refusal, unsupported country, POST-only resolve route, status route, and strict visitor-content rejection.

### Safety branch
- GitHub Actions run #42606711297: success.
- Python compile of Safety and Guide modules.
- V488 Safety Boundary QA.
- Safety state-machine regression tests: first-turn fast path, no-HRN follow-up, deterministic transition matrix, stage recovery from serialized history, two-step recovery/release, EI outage continuity, emergency-contact classification, and no-HRN snapshot.
- The tests import the Guide runtime and verify the standalone safety contract. The latest Safety branch run #42606711297 passed.

## Mini-USE infrastructure boundary
Mini-USE Workspace was inspected read-only. The existing Catalogue production, stewardship, and candidate services were not repurposed, reconfigured, redeployed, or replaced. No new Render service was created.

## Remaining release blockers
1. **Safety-session integrity:** stage continuity currently relies on serialized conversation history supplied with the request. A server-side signed safety-state token or equivalent authenticated session ledger is needed before production to prevent state tampering and strengthen continuity.
2. **Country parity:** the EI registry currently covers five countries, not the ten-country target.
3. **Source review:** HTTPS URL and provenance structure checks do not prove that the source supports the claimed service, coverage, or availability. Every record needs human verification against authoritative sources.
4. **Visitor-facing E2E:** no browser E2E has been run against the actual Guide visitor interface. The standalone EI plugin is an API/resource subsystem, not a visitor UI. A safe WordPress/Guide staging target is required; production must not be used.
5. **Safety content review:** the transition sequence and wording have been ported from the protected deterministic baseline, but the standalone wording and all stage transitions still need a final human safety review.
6. **Remote updates:** cryptographic signatures, trusted-key provisioning/rotation, and replay protection are not implemented. Remote updates must remain disabled.
7. **Service arbitration:** contextual prioritization and full taxonomy coverage need additional specification and country-specific tests.

## Release decision
**NO-GO for production deployment or merging into production.** The development branches demonstrate the intended separation and pass their current isolated validation gates. The remaining blockers above must be closed and reviewed before any release.

No production WordPress files, settings, plugins, databases, Render services, deployments, or live registry records were changed.
