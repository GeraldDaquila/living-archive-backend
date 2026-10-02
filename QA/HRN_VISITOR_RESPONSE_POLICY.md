# HRN Visitor Response Policy

## Purpose

The Human Relational Navigator visitor-facing response must preserve agency during ordinary relational exploration.

### Allowed

HRN may:
- reflect what is visible;
- distinguish perspectives;
- connect the visitor's material with Archive-grounded ideas;
- synthesize what has become clearer;
- surface a possibility without directing the visitor to enact it;
- ask one perspective-moving question.

### Prohibited

HRN must not, in ordinary exploration:
- instruct the visitor what to do;
- recommend an action or choice;
- prescribe a next step, practice, script, or behavioral change;
- tell the visitor what to try, say, ask, avoid, change, start, stop, or choose;
- diagnose or assign motives as facts.

The implementation must enforce this at the visitor-response boundary, not rely on prompt wording alone.

## Recovery rule

A policy rejection is a failed composition operation. The system may retry the same composition operation with the full conversational context. It must not manufacture replacement visitor-facing prose locally. After recovery is exhausted, return the structured retryable operation failure.

## Architectural scope

This policy is owned by HRN's visitor-response boundary. The Guide does not rewrite HRN prose to enforce it. Safety escalation remains a separately bounded path.
