# EI / HRN Protected Baseline and Test Contract
Date: 2026-11-09
Development branch: `dev/ei-security-and-hrn-adapter-20261109`
Parent source snapshot: `archive/live-ei-hrn-baseline-20261109`
Production changes: none.

## Frozen HRN safety boundary
The complete captured HRN plugin file is pinned by Git blob SHA:
- `plugins/human-relational-navigator/human-relational-navigator.php`
- Baseline blob SHA: `c5b4df0a8985f5c8379e468a9efafac1c827f019`

Protected methods and request-order invariants:
- `deterministic_safety_signal()`
- `explicit_suicide_language()`
- `safety_answer_class()`
- `safety_transition()`
- `safety_response()`
- `rest_handler_inner()`

The safety firewall must run before ordinary relational interpretation. When a safety state is active, HRN remains in control of answer classification, state transition, intervention language, and next question. EI may return resource data only. No EI error may suppress or delay HRN's intervention response.

Any future HRN source change must be reviewed against this baseline and the regression suite. The baseline blob SHA is a source-control reference, not a cryptographic filesystem checksum.

## EI baseline file references
- Main plugin: `581e4c42a7b8de6c9fb8a86b317328d0bb4e4fdd`
- Registry: `32214d52b21b95d7f9cd1a7b4dbefba6ffa966c4`
- Location resolver: `c9623c4de50e9e7be3866e4805f7a9be45e64b8d`
- Selector: `6600da3bda5762e609c34ca10914388237198fff`
- Engine: `51f484e2c24f82ca05413bfb719958d18d18b9c8`
- Presenter: `f8964ffbf8a9d358da5a31ce6186b7c98669931c`
- API: `d46fef14033c8105baf3da19c28fcddd1fd9efb9`

## Security change made on this development branch
The EI update manager's `check_now()` has been changed to fail closed:
- It records the check timestamp and returns `disabled_security_gate`.
- It performs no remote HTTP request.
- It cannot accept or activate a remote registry candidate.
- It leaves the local registry file untouched.
- It does not call HRN and cannot advance or suppress the HRN safety state machine.

Reason: there is no implemented cryptographic signature verifier or provisioned trusted public key. A content hash is not a publisher-authentication mechanism. Remote updates must remain disabled until signature verification, key provisioning/rotation, replay protection, and positive/negative tests exist.

This is a development-branch change only. It has not been deployed to WordPress.

## Mandatory test contract

### A. Protected HRN safety regression
1. Green state + no signal -> ordinary HRN path remains available.
2. Green state + deterministic amber signal -> safety response before ordinary interpretation.
3. Green state + deterministic red signal -> acute safety response before ordinary interpretation.
4. Explicit suicide language triggers safety firewall.
5. Current-stage yes/no/uncertain/refusal preserve current transition contract.
6. Acute-stage yes advances only as specified by the existing transition function.
7. Acute-stage no/uncertain/refusal remains in bounded follow-through.
8. Acute connection language distinguishes contact capability from physical presence.
9. EI timeout/exception/invalid response does not alter safety state or question.
10. HRN still returns its safety response if EI is unavailable.

### B. Location-only operation invariance
For every active safety state, capture the exact input safety stage and question, submit a country-only location operation, and assert:
- stage is byte-for-byte unchanged;
- question is byte-for-byte unchanged;
- answer classifier is not invoked;
- transition function is not invoked;
- no ordinary relational interpretation is invoked;
- only resource location/resolution data changes.
Also test conflicting country evidence and explicit visitor correction.

### C. EI registry and security
1. Local registry parses and validates.
2. Invalid JSON is rejected without replacing the active registry.
3. Missing required structure is rejected.
4. Duplicate country/resource/verification IDs are rejected.
5. Unknown country/architecture/verification references are rejected.
6. Unsupported country is distinguished from unknown country.
7. Resource verification must be active, in-scope, evidence-backed, and within review period.
8. Expired `review_due` or stale verification cannot be selected.
9. Unsigned remote candidate is rejected.
10. Missing signature is rejected.
11. Invalid signature is rejected.
12. Signature from an untrusted key is rejected.
13. Replayed/older registry version is rejected.
14. Corrupt content hash is rejected.
15. Failed activation preserves last-known-good local registry.
16. Registry update check never blocks the active emergency response.

### D. Taxonomy and contextual selection
Verify explicit mapping for:
- `general_emergency`
- `police`
- `fire`
- `medical`
- `rescue`
- `traffic`
- `crisis_support`
- `mental_health_support`
- `emotional_distress`
- `suicidal_crisis`

Test medical prioritization, immediate physical danger, acute state, crisis-only need, China police/medical distinction, primary/secondary alternatives, no-match behavior, and confidence/provenance reporting.

### E. Ten-country parity and data provenance
Test PH, US, DE, GB, CN, CA, AU, SG, HK, NL. Every record must have independently checked source evidence, exact service scope, contact channel, coverage, verified date, review due date, and status. Legacy HRN entries are migration leads only, not automatic proof of validity.

### F. Browser end-to-end
- Safety prompt appears and is actionable.
- Location prompt does not enter the safety-answer pathway.
- Country-only submission updates resource options only.
- Unknown/refused/unsupported location is clearly handled.
- EI outage leaves HRN safety conversation operational.
- No duplicate, contradictory, or stale resource cards.
- Mobile and desktop interaction, keyboard access, and tel links are tested.

## Release gates
No production rollout until:
1. The adapter is complete and isolated from HRN safety logic.
2. All test groups A–F pass.
3. Resource records are independently verified.
4. Mandatory signature verification is implemented and proven with positive and negative tests.
5. A current production checkpoint and recoverable source package exist.
6. A reviewed release plan and rollback procedure are approved.

## Current status
- HRN baseline pinned: yes.
- EI remote update fail-closed patch on development branch: yes.
- PHP lint/runtime test: not yet run.
- HRN adapter: not yet implemented.
- Location-only correction: not yet implemented.
- Resource re-verification: not yet completed.
- Full E2E: not yet run.
- Production deployment: prohibited at this stage.
