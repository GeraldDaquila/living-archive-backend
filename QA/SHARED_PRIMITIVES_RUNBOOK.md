# v487.83 Shared Primitives Runbook

## Verified scope

The isolated primitive module is intended to be pure infrastructure. It may be imported by QA and future
mode implementations, but it is not currently imported by production.

## Regression expectations

The primitive suite must preserve:
- clean source text while removing markup and URLs;
- HTTPS-only evidence and doorway URLs;
- deterministic de-duplication;
- source-linked claims without inventing evidence references;
- explicit epistemic treatment;
- explicit READY / DELEGATE / NEEDS_RETRY / UNAVAILABLE states;
- rejection of internal protocol objects at the visitor-language boundary.

## Integration rule

A future production seam may replace one existing transformation at a time. Each seam must have a
before/after regression case, and protected production hashes must be checked before and after the change.

No visitor-facing answer builder is to be moved into this module.
