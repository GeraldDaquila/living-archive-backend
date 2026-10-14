# General Purpose Guide — Frozen Gold-Standard Benchmark

**Status:** FROZEN  
**Benchmark:** `tests/fixtures/general_guide_stewardship_gold_standard.json`  
**Accepted on:** 2026-10-14  
**Scope:** Visitor-facing General Purpose USE / The Guide

The fixture records the accepted stewardship answer and the observable structural requirements for regression testing. Treat it as a read-only reference. It is not permission to revise the response, loosen the requirements, or change the frozen standard to match current behavior.

## Required behavior

- Answer the visitor's question directly and completely before showing any navigation.
- Preserve the reference answer's three connected movements: meaning, why ordinary choices matter, and the boundary between responsible care and control/self-sacrifice.
- Keep the Archive doorway separate and optional.
- Honor the visitor's explicit request not to be sent to another page.
- Render after the first Search submission; no second press may be required.
- Assess answer composition and doorway behavior, not just transport success, HTTP status, or response length.

## Change control

Do not edit the expected answer or its invariants to make a failing build pass. If the user explicitly authorizes a new gold standard, create a separately versioned benchmark and document the reason; retain this fixture as the historical reference.

The protected `use_core.py` file remains out of scope and must not be modified.

## Verification boundary

Unit and backend JSON/SSE tests are necessary but insufficient. The release gate also requires a real visitor-facing browser submission with confirmation that the first click renders the answer and optional doorway correctly, without a connection error or direct handoff. Do not report full end-to-end QA as passed until that browser behavior has been observed.
