# Lean Core Dependency Findings — Pass 1

## Scope
Read-only dependency trace following the verified pre-housekeeping baseline.

## Finding A — Legacy exact-answer authority is isolated and removable in principle
`general_guide_gold_standards.py` currently loads `USER_APPROVED_GOLD_STANDARD` and `FROZEN_REFERENCE_ONLY` into exact-answer authority. The cross-question leakage detector already excludes frozen references.

**Cleanup candidate:** restrict exact runtime authority to current user-approved Gold Standards after targeted tests prove no current production contract intentionally depends on legacy frozen exact-query answers.

**Risk:** an exact historical frozen benchmark would receive the normal contemporary Guide answer rather than a legacy canned response. This is a deliberate behavior change and requires validation.

## Finding B — Current shadow learning is lean
`gold_star_lessons.py` loads only current user-approved Gold Standards and uses the qualitative review only as governance metadata.

**Decision: KEEP.**

## Finding C — HRN retirement is primarily a terminology boundary
The request boundary states HRN is retired while relationship capability remains native to The Guide.

**Decision: do not delete functional relationship code merely because comments retain legacy vocabulary.**

## Next trace gates
1. Inspect tests encoding frozen-reference behavior.
2. Trace historical JSON artifact references before archival or deletion.
3. Trace relationship contribution imports before terminology cleanup.

No runtime changes are made by this audit pass.
