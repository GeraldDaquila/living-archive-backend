# CLSS Hybrid Synthesis — Isolated Integration Contract

**Status:** experimental adapter integrated with the USE Provider Bank capability contract on this isolated branch; not connected to WordPress or any production request path.

## Purpose

Combine deterministic evidence handling with an optional model-generated candidate while retaining deterministic authority over input normalization, consent gating, structural validation, and fallback. A model candidate is not a finding and is never visitor-displayable until a separate semantic review process has accepted it.

## Current boundary

- The current CLSS WordPress experience remains session-only and does not submit answers to a server.
- The adapter has no direct provider transport or credentials. Its optional `UseProviderCandidateBuilder` delegates to USE's in-process `provider_gateway_service.execute`, which routes only through Provider Bank.
- Provider Bank now exposes a dedicated `clss_synthesis` operation with structured reasoning capability requirements and a 1,200-token operation floor.
- The adapter does not log or persist answer text. It reports provider invocation and transmission separately when the real USE builder is used.
- Tests use an injected mock gateway executor. No real provider call or real visitor-answer transmission has been performed.
- The new capability is present only on the isolated Git branch. It is not in the live `main` branch or active Render runtime.
- Missing answers remain gaps; third-party private intent and suitability remain outside scope.

## Consent and minimization

Candidate request preparation requires all three exact fields: `granted: true`, purpose `clss_synthesis`, and notice version `clss-synthesis-notice-v1`. This is a software gate, not proof that an adequate public disclosure has been deployed.

The request includes only evidence IDs, prompt IDs, dimensions, source types, answer text, and minimal provenance. Optional free-text context, affected-party fields, and other optional context fields are excluded. Each answer is capped at 4,000 characters, total answer text at 16,000 characters, and evidence count at eight.

## Candidate acceptance

The shared CLSS response validator checks structure, allowed evidence IDs, mode consistency, and prohibited language. It explicitly does **not** establish semantic entailment. Therefore a structurally valid model candidate is labelled `unverified_candidate` and requires human semantic review. Invalid output or builder failure selects the deterministic fallback.

## Required next gates

1. Complete semantic evaluation against the five core fixtures: strengths-only, concern-only, mixed, contradictory, and sparse; retain existing CLSS regression fixtures as well.
2. Add adversarial tests for fabricated evidence, unsupported causal claims, provenance laundering, overconfident wording, hidden-motive inference, and missing-data penalties.
3. Independently review provider logging, tracing, retention, subprocessors, and request-body handling before any live transport.
4. Implement visitor-facing notice and explicit opt-in in a separate reviewed WordPress change. The present production UI must not silently transmit answers.
5. The dedicated Provider Bank operation and gateway allowlist are now implemented and contract-tested on this isolated branch. Next, audit provider logging/tracing/retention/subprocessors, complete synthetic model evaluation and independent human semantic review, then implement a separately reviewed authenticated CLSS entry route and visitor-facing opt-in. Do not deploy or merge this capability before those gates.

## Release decision

**NO-GO for production integration.** The USE gateway capability is integrated in the isolated branch, but no CLSS entry route is wired, no provider has been invoked for CLSS, no visitor answers have been transmitted, and no public privacy claim or visitor experience has changed.
