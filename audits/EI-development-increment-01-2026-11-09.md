# EI Development Increment 01 — Security and Selection Guardrails
Date: 2026-11-09
Branch: `dev/ei-security-and-hrn-adapter-20261109`
Base: `archive/live-ei-hrn-baseline-20261109`

## Changes committed
1. **Remote registry updates fail closed.** `LAEI_Update_Manager::check_now()` records the check timestamp and returns `disabled_security_gate`. The remote HTTP fetch and activation path has been removed from this method. No remote registry candidate can be accepted until a trusted public key and cryptographic signature verifier are implemented and tested.
2. **Verification freshness is enforced at selection.** A resource is eligible only if its verification status is `verified`, both dates are ISO `YYYY-MM-DD`, `verified_at` is not in the future, `review_due` has not passed, and the review date is not before the verification date.
3. **Resource confidence no longer treats stale verification as high confidence.** The location resolver checks verification dates before returning high resource-selection confidence.
4. **Unsupported countries and service needs are distinguished.** The selector now returns explicit failure states for unsupported country, invalid service need, no matching service, and expired verification.
5. **Service aliases added.** `emergency` maps to `general_emergency`; `emergency_medical` and `medical_emergency` map to `medical`; `crisis` maps to `crisis_support`; `mental_health` maps to `mental_health_support`; `suicide_crisis` maps to `suicidal_crisis`.
6. **Eligible alternatives are returned.** The selector now includes other eligible resources as `secondary`; the presenter exposes their names and telephone actions separately from the primary resource.

## Safety boundaries preserved
- No HRN file was changed in this development increment.
- No HRN risk recognition, answer classification, transition, intervention wording, or safety REST flow was changed.
- No production WordPress file, option, registry, or deployment was changed.
- The local EI registry remains the source used by EI; remote updates are disabled.

## Live registry shape observed (not yet independently reverified)
- Registry version: `2026.10.13.001`
- Countries: PH, US, DE, CN, GB (5)
- Resources: 10
- Verification records: 9
- Service types represented: crisis_support, emotional_distress, fire, general_emergency, medical, mental_health_support, police, rescue, suicidal_crisis, traffic.
- The resource set does not yet cover the full ten-country HRN legacy footprint (CA, AU, SG, HK, NL are absent).
- Verification records currently carry `verified_at`, `review_due`, `verification_scope`, `source`, and `evidence_type`. The current selector enforces status and date freshness; deeper source/evidence and scope validation remains to be implemented.
- HRN's CN 120 medical resource is now mapped through the EI `emergency_medical` alias to the EI `medical` taxonomy.

## Validation status
- Source-control comparison confirms only five EI files plus the test-contract document differ from the parent baseline.
- HRN source remains unchanged from its pinned baseline blob.
- Text-level review of the changed methods completed.
- PHP lint/runtime execution: not available in this connector workflow; **not claimed as passed**.
- Automated unit tests: not yet implemented or run.
- Browser E2E and HRN integration: not yet implemented or run.
- Production deployment: prohibited.

## Next required work
1. Implement a dedicated location-only resolver operation and HRN adapter without changing protected safety methods or call order.
2. Validate registry structure, evidence completeness, verification scope, and review dates on local load and candidate validation.
3. Design and implement mandatory cryptographic signatures with trusted-key provisioning, rotation, anti-replay, and negative tests. Until then, remote updates stay disabled.
4. Independently reverify all 10-country resources and complete the missing five countries only when authoritative sources support each record.
5. Add executable tests in the repository's actual test harness, then run PHP lint, unit tests, WP integration tests, and browser E2E before release review.
