# Emergency Intelligence / HRN Source Audit
Date: 2026-11-09
Scope: Read-only review of the 18-file live-site text snapshot on branch `archive/live-ei-hrn-baseline-20261109`.
Production status: No WordPress files, settings, registry records, or deployments changed.

## Executive finding
The intended separation is architecturally sound, but the current EI plugin is not yet a safe replacement for HRN's resource-resolution path. HRN's safety state machine remains self-contained and has no call to the EI public resolver in the captured source. The migration must be additive and gated; do not retire HRN's embedded registry yet.

## Protected HRN boundary
The captured HRN source contains deterministic functions:
- `safety_answer_class()`
- `safety_transition()`
- `safety_response()`
- `deterministic_safety_signal()`
- `explicit_suicide_language()`
- `rest_handler_inner()`

The REST handler evaluates the deterministic safety signal and explicit suicide language before ordinary relational interpretation. When safety is active, it calls the answer classifier and transition function, then returns a safety response. These functions and the order of this firewall are protected. EI must not classify risk, interpret answers, select safety states, or advance intervention stages.

## Confirmed integration gap
A search of the captured HRN PHP source found no reference to:
- `living_archive_emergency_resolve`
- `living-archive/emergency`

HRN still owns the ten-country embedded resource registry, country normalization, emergency/crisis selection, and Find A Helpline fallback. The EI plugin is therefore not yet integrated into the captured HRN request path.

## Confirmed EI defects / blockers
1. **Unsigned remote registry can be accepted.** In `check_now()`, signature rejection occurs only when the candidate sets `signature_required`. If that flag is absent/false, the code proceeds to write/activate the candidate after schema validation and optional content-hash validation. A hash is not authenticity. Remote updates must remain disabled until a trusted public key and mandatory signature verification exist.
2. **Verification freshness is not enforced.** `validate_candidate()` checks that verification records contain fields and that resources reference an existing record. The selector checks `status === verified`, but does not enforce `verified_at`, `review_due`, verification scope, or evidence freshness.
3. **Registry load validation is incomplete.** `load()` checks only JSON parsing and `validate_structure()`; it does not apply full candidate validation to the local active registry.
4. **Service taxonomy / semantic mapping is incomplete.** The selector matches exact `service_types`, with a single alias from `emergency` to `general_emergency`. There is no confirmed mapping for HRN needs such as `emergency_medical`, `police`, `fire`, `rescue`, `crisis_support`, `mental_health_support`, `emotional_distress`, and `suicidal_crisis`.
5. **Context-sensitive selection is missing.** The EI selector ignores `safety_state` when scoring and returns the first priority-sorted item. It does not reproduce HRN's medical-need prioritization (medical +500; immediate danger +300; acute +100).
6. **Alternatives are not implemented.** EI always returns an empty secondary list; presenter also emits no secondary options.
7. **Failure states are collapsed.** The selector's fallback distinguishes only unknown/refused location from a general fallback. It does not clearly distinguish unsupported country, no matching service, expired verification, or registry unavailable.
8. **Location evidence requires refinement.** Explicit user statement and browser geolocation both have high weight; conflicts are recorded but highest-strength evidence silently wins. An explicit current statement should be authoritative for the current location, with conflicts surfaced to the visitor where relevant.
9. **Resource confidence can be overstated.** Location resolver marks resource confidence high if any verified general-emergency resource exists, without checking freshness, country support status, or service-specific coverage.
10. **Emergency service model is too narrow.** Presenter handles one selected item or equivalent numbers, but no contextual medical/police/fire differentiation or governed secondary directory options.

## HRN location-only defect
The frontend location prompt currently routes the visitor's country response through the ordinary HRN REST turn as a message, including an acute safety stage/question. That allows a location string (for example, “Philippines”) to be interpreted by the active safety answer classifier. The correction must be a dedicated location/resource-resolution operation. It must not call `safety_answer_class()` or `safety_transition()`, and must preserve the existing safety stage and safety question byte-for-byte.

## Required migration contract
HRN retains:
- deterministic risk recognition;
- safety state machine and transitions;
- safety intervention wording and sequence;
- safety answer classification;
- frontend safety conversation.

EI owns:
- canonical resource registry;
- location normalization and evidence/provenance;
- service taxonomy and mapping;
- verification lifecycle and expiry;
- context-sensitive resource selection;
- primary and secondary alternatives;
- governed fallback and failure states.

HRN calls EI only for resource resolution and presentation data. EI failure must never block or reset HRN's active safety intervention.

## Required implementation gates
1. Independently verify every canonical resource record and source; do not promote legacy HRN entries solely because they exist.
2. Define the canonical taxonomy: `general_emergency`, `police`, `fire`, `medical`, `rescue`, `traffic`, `crisis_support`, `mental_health_support`, `emotional_distress`, `suicidal_crisis`.
3. Enforce verification freshness, scope, evidence, review-due date, active status, and fail-closed registry validation.
4. Require cryptographic signatures for every remote update; reject unsigned, invalidly signed, stale, or replayed candidates.
5. Implement HRN adapter and location-only operation without touching protected safety functions.
6. Run 10-country parity, taxonomy, medical-prioritization, crisis, alternatives, China service distinction, unknown/refused/conflicting location, expired verification, signature rejection, EI outage, and location-stage-invariance tests.
7. Run full HRN safety regression and browser E2E before any production rollout.
8. Retain HRN's existing registry as a temporary fallback until parity and E2E gates pass; retire it only in a separately reviewed change.

## Snapshot limitation
The 18 expected files are present on this branch and fetched text matches the text returned by the live-site reader. The large HRN PHP source was returned by the reader as 552,896 characters while the reader's filesystem byte-size field reported 553,170 bytes. This is a UTF-8 byte/character distinction, not evidence of a truncated transfer. However, no independent raw filesystem hash or full plugin-directory archive has been captured. This branch is a text-level source baseline, not yet a certified byte-for-byte filesystem backup.

## Decision
**NO-GO for production integration or retirement of the HRN registry.** Proceed with implementation only on a separate development branch after the canonical registry and update-security design are corrected and the protected HRN baseline is explicitly frozen.
