# CLSS Hybrid Synthesis — Isolated Integration Contract

**Status:** experimental adapter; not connected to WordPress, USE, Provider Bank, or any production request path.

## Purpose

Combine deterministic evidence handling with an optional model-generated candidate while retaining deterministic authority over input normalization, consent gating, structural validation, and fallback. A model candidate is not a finding and is never visitor-displayable until a separate semantic review process has accepted it.

## Current boundary

- The current CLSS WordPress experience remains session-only and does not submit answers to a server.
- This adapter performs no HTTP calls, provider routing, logging, persistence, or telemetry.
- An injected candidate builder is used only for offline/mock tests.
- No real visitor answers may be passed to a provider through this module.
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
5. Only after those gates, propose a separate Provider Bank operation and gateway contract change. Do not alter USE `main.py` or provider pools as part of this isolated adapter.

## Release decision

**NO-GO for production integration.** This branch is a testable seam only. No live route, public privacy claim, or visitor experience is changed.
