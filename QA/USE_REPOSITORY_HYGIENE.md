# USE Repository Hygiene & Architecture Boundary

## Purpose

This is housekeeping, not a runtime redesign. The repository is being kept small around the
working production path while preserving historical work in Git history.

## Current architecture

**The Guide / USE is the macro hub.**

- USE interprets the visitor request and determines the appropriate kind of movement.
- Specialist tools are narrow spokes, such as Seeing the Relationship (HRN) and FSD.
- Canonical Living Archive assets remain the authoritative content layer.
- A general utility capability may be used when no suitable specialist exists.
- USE owns orchestration, contribution validation, canonical navigation, and final integration.

**Visitor → USE → route/delegate/retrieve → spoke or asset or general utility → contribution → USE → next canonical doorway**

The general utility capability is a fallback instrument of USE, not a competing specialist.

## Working boundary

Protected at this cleanup checkpoint:

- use_core.py
- main.py
- main_v487_28_runtime.py
- specialist_registry.py
- specialist_adapters.py
- relationship_contribution.py
- relationship_adapter.py

No runtime behavior is intentionally changed by this housekeeping change.

## Housekeeping classification

**KEEP / PROTECT:** current production runtime, specialist pipe files, HRN policy tests/docs, requirements and deployment configuration.

**CONSOLIDATE:** versioned CI gates that duplicate current runtime checks or enforce obsolete release identities.

**ARCHIVE:** historical validation scripts/tests. Git history preserves their exact prior state.

**REMOVE:** obsolete GitHub Actions workflows from v335-v387 that still execute against main/PRs.

## Evidence

A 2026-10-02 run of the v340-named workflow compiled the production modules successfully, then failed in
run_v338_validation.py on the retired assertion `APP_VERSION = "v340"`. That is CI noise, not protection
of the current runtime.

## Version identity note

Git main is at the v487.77 merge commit while main.py still declares v487.76. This is metadata drift, not
a runtime behavior change. It is recorded here and deliberately left for a dedicated identity-normalization
pass.

## Future guardrails

The single current validation path should check protected assets, importability of the specialist pipe,
delegation boundaries, specialist-voice preservation, and rejection of reintroduced legacy CI.
