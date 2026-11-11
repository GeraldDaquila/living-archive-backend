# Lean Core Housecleaning Audit — v1

## Purpose

Reduce active architectural weight before further Gold Star development. The standard is not the smallest repository; it is the smallest coherent runtime and governance surface that preserves current Guide quality, safety, resilience, and testability.

## Confirmed findings

### 1. Legacy Gold Star authority boundary — CLEAN, with one simplification opportunity

- `general_guide_gold_standards.py` still treats `FROZEN_REFERENCE_ONLY` as eligible for exact runtime resolution.
- The current architectural direction is that legacy standards no longer carry active quality authority merely because they were historically frozen.
- **Recommendation: review and remove `FROZEN_REFERENCE_ONLY` from runtime answer authority after confirming no current production contract depends on it.**
- Historical records should remain provenance or QA material, not visitor-answer authority.

### 2. Active Gold Star shadow layer — KEEP

`gold_star_lessons.py` is compact, explicitly limited to `USER_APPROVED_GOLD_STANDARD`, metadata-only, abstention-capable, and isolated from visitor-facing composition.

**Recommendation: keep as core muscle.**

### 3. Historical transfer-review artifacts — CONSOLIDATE / ARCHIVE

The repository now contains multiple historical Gold Star analysis artifacts created during the transition:

- `gold_star_transferability_map.json` — superseded by the qualitative review.
- `gold_star_historical_revalidation_audit.json` — governance history, not runtime input.
- closed PR #1211's proposed historical best-practice harvest — explicitly not part of the active architecture.

**Recommendation: retain governance history outside the active runtime surface; remove superseded maps from active documentation paths once tests and references are checked.**

### 4. HRN terminology in native relationship integration — REVIEW, NOT DELETE BLINDLY

The standalone HRN architecture is retired, but some current relationship contribution contracts retain HRN wording to describe historical voice provenance.

The active code also explicitly states that no separate HRN specialist is registered.

**Recommendation: audit terminology and comments separately from functional relationship capability. Do not remove the relationship contribution boundary merely because its comments contain legacy vocabulary.**

### 5. Safety path — KEEP

Safety is explicitly standalone, deterministic, and HRN-independent. It is active architecture, not legacy scaffolding.

**Recommendation: no retirement action.**

## Required next audit passes

1. Trace every import and runtime call for `general_guide_gold_standards.py`.
2. Trace references to each historical Gold Star JSON artifact and test.
3. Identify dead HRN-named modules versus active relationship contributions.
4. Inventory duplicate shadow/telemetry mechanisms and determine whether they serve distinct purposes.
5. Produce deletion candidates only after proving they have no runtime, QA, or deployment dependency.

## Governance rule

No artifact is deleted merely because it is old. No artifact is retained merely because it might someday be useful. Git history preserves implementation history; the active codebase should preserve only present capability, necessary quality controls, and deliberate institutional memory.
