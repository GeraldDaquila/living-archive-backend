"""Instrumented provider-envelope measurement plan for v334 release control.

This module is intentionally non-production. It documents the exact runtime
objects that must be measured after temporarily substituting the existing
COMPACT_GENERATION_SYSTEM_PROMPT for the current GENERATION_SYSTEM_PROMPT.

The production builder already centralizes provider-message assembly; the
controlled implementation should change only that prompt selection, then use
_build_generation_messages() and _estimate_message_chars() for the real gate.
"""

MEASUREMENT_TARGET = {
    "normal": "_build_generation_messages(user_query, intent, '', orientational_frame, compact=False)",
    "compact": "_build_generation_messages(user_query, intent, '', orientational_frame, compact=True)",
    "estimator": "_estimate_message_chars(messages)",
    "recommendation_reservation_tokens": 256,
    "max_provider_input_chars": 3800,
    "max_provider_total_chars": 4600,
}

REQUIRED_ASSERTIONS = (
    "fixed normal envelope < 3800",
    "fixed normal envelope + estimated recommendation output <= 4600",
    "compact envelope < 3800",
    "compact envelope + estimated recommendation output <= 4600",
    "positive canonical evidence capacity remains",
    "known grief recommendation reaches real provider generation",
)

PROBES = (
    "What advise or essay from the Living Archive that you can recommend for someone who is grieving from the the death of a love one?",
    "What is grief?",
    "What essay can you recommend for someone grieving?",
    "I'm not sure what I'm looking for yet, but I want to explore.",
)

print("v334 provider-message measurement target prepared; run against the exact production builder before integration.")
