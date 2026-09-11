# USE v334 Lean Prompt Measurement Result

## Status

MEASUREMENT HARNESS VERIFIED; EXACT PRODUCTION MESSAGE SHAPE STILL REQUIRED BEFORE CODE INTEGRATION.

The static harness is intentionally conservative: it mirrors the configured provider limits and the live recommendation completion reservation, but it does not import `use_core.py` and therefore does not claim that its fixed-input result is identical to the production `_build_generation_messages()` result.

## Why the exact production measurement matters

The production builder can add user-message structure, intent/orientation material, and other operational fields around the system prompt. The historical live failure was measured from the real builder at approximately 4.6K fixed characters. Therefore the lean prompt can only be accepted after the real builder reports a fixed envelope that leaves positive evidence capacity while retaining the 256-token recommendation reservation.

## Release gate

Do not integrate the lean prompt into production until:

1. the exact production `_build_generation_messages(..., generation_context="", compact=False)` measurement is recorded;
2. the exact compact measurement is recorded;
3. at least one real provider candidate passes preflight with the recommendation reservation;
4. the known grief query executes through provider generation rather than deterministic fixed-envelope fallback;
5. the resulting answer retains canonical recommendation identity, source-grounded fit, and the v334 compassionate boundary.
