# USE v334 Lean Prompt Branch Audit

## Branch

`v334-release-control`

## Current controlled code

The branch `main.py` now contains `_LEAN_PROVIDER_SYSTEM_PROMPT` and routes provider-message construction through it via `_v334_build_generation_messages`.

The substitution is intentionally limited to the provider system envelope. The established `_original_build_generation_messages` call still supplies the existing user/evidence message structure, while the v334 post-generation compassionate boundary remains active.

## Required next verification

Before promotion, verify the exact runtime behavior from the controlled branch:

1. Compile `main.py` and `use_core.py`.
2. Measure `_build_generation_messages` with empty evidence for normal and compact paths.
3. Confirm both fixed envelopes are below the configured provider input limit and that the 256-token recommendation reservation leaves positive total capacity.
4. Run the benchmark grief query through the controlled deployment.
5. Confirm provider generation executes rather than deterministic fixed-envelope fallback.
6. Confirm the answer identifies the adjudicated primary recommendation and provides source-grounded fit/context without asserted visitor benefit.
7. Run normal topical, exact-title/link recommendation, and open-exploration regression probes.
8. Verify the complete changed unit, including source identity/build identity behavior, before any production promotion.

## Promotion state

Production `main` remains unchanged until all gates above pass.
