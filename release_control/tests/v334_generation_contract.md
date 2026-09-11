# USE v334 Generation Contract Gate

## Baseline
- Production baseline: `main` commit `5a68007789c49d6ea067eeb4da66315e9163bf21`.
- Core engine: intact v333 `use_core.py`, blob `fb3208a8d287f16562ffd640d89f65d5e8d18607`.
- Current observed provider preflight failure: fixed input approximately 4.6K chars before evidence; estimated output reservation 1280 chars at 256 max completion tokens.

## Next intervention
Reduce duplicated fixed provider instructions in the generation envelope. Do not reduce or bypass canonical evidence, recommendation authority, provenance, sovereignty, or the v334 vulnerable-experience boundary.

## Required invariants
1. The provider receives exact canonical title/URL identity only from supplied evidence.
2. Singular recommendation questions retain the adjudicated primary resource as authority.
3. The provider does not receive internal audit/process commentary as visitor-facing instruction.
4. Vulnerable-experience questions retain the v334 prohibition on asserted visitor benefits, prescriptions, and personal outcomes.
5. The finished answer remains visitor-facing and navigation-oriented.

## Budget gate
The revised envelope must be measured using the existing `_estimate_message_chars()` and `_fit_generation_context_to_provider_budget()` machinery.

Target: reduce fixed system/user envelope materially below the observed ~4597-character failure point while leaving enough capacity for substantive canonical evidence and the configured completion reservation.

The change is not eligible for production promotion until the provider preflight can execute at least one real generation path without immediately failing on the fixed envelope.
