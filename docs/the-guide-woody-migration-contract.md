# The Guide Woody Migration — Baseline-Preserving Contract

Status: migration design / QA only. This document does not authorize or perform a production switch.

## Known-good reference

- Public page: https://geralddaquila.com/the-guide/
- WordPress page ID: 76925
- Restored revision: 78716 (created 2026-10-15 21:06 GMT; October 16 in Manila)
- Rollback revision created: 78829
- Current baseline controller URL in restored page: /wp-content/uploads/2026/10/living-archive-guide-v489.245.js
- User-provided screenshot confirms the restored Custom HTML form submitted the stewardship question and rendered a substantive answer with a continuation link and Start another question control.
- Cache was flushed for post 76925 after restoring the revision.
- This is evidence for the baseline question path, not proof of every specialist/follow-up route.

## Intended destination

A reusable Woody Snippet/shortcode instance for The Guide, hubs, and cornerstones. The live baseline remains unchanged until the candidate passes the gates below.

## Concrete risk found in candidate v489.246.2

The Woody wrapper carries `data-guide-instance="woody"`, but the retrieved controller excerpt includes document-wide lookups such as `document.getElementById('archive-response-text')` and `document.getElementById('archive-response-box')`. These lookups are not instance-scoped. With multiple embedded instances or duplicate IDs, the controller can address the wrong response surface. This is a source-level risk; a cross-instance failure has not yet been demonstrated.

## Required migration rules

1. **Baseline preservation:** retain the restored Custom HTML page and controller as a rollback reference. Do not overwrite either while developing the candidate.
2. **Single owner per instance:** each instance must own its form submit handler and must not cancel or hijack another instance's events.
3. **Instance-scoped DOM:** resolve input, submit button, response, recommendation, safety UI, reset controls, and follow-up panel from the instance root. Do not use document-wide ID lookups for instance-owned nodes.
4. **No duplicate-ID dependency:** either remove IDs from reusable internals in favor of classes/data attributes or generate unique IDs per instance and maintain correct label/ARIA references.
5. **One request per submit:** a single user submit creates exactly one POST to /api/query. The request includes the exact visitor question.
6. **Visible substantive response:** response area becomes visible and contains at least 80 characters of non-placeholder content.
7. **Routing parity:** verify specialist handoffs, not just ordinary responses; the controller must preserve the existing intent-specific navigation behavior.
8. **Follow-up parity:** verify safety follow-up and ordinary continuation; each remains attached to the originating instance.
9. **Multiple-instance isolation:** mount two shortcode instances on a QA-only page; submit to one and verify the other instance's input, response, and controls remain unchanged. Then submit to the second and verify each answer stays in its own instance.
10. **Production gate:** do not replace the live baseline until the browser E2E run passes all applicable gates and the exact candidate source is preserved with a versioned artifact.

## Current QA evidence and limitations

- The Woody browser E2E found the wrapper and filled the agreed stewardship question, but the Playwright click stalled before a confirmed POST. No successful Woody request/answer was established.
- The isolated upper-entryway workflow did not yet establish a clean baseline run; its selector/diagnostic code timed out. The user screenshot is the current positive evidence for the baseline question path.
- The retrieved controller source was truncated by the available read response, so a complete source-to-source comparison has not been certified.
- No production Woody migration is approved by this document.

## Exit criteria

Mark Woody migration ready only when:
- full candidate controller source is recoverable and preserved;
- the single-instance E2E passes submission, request count, response rendering, and controls;
- specialist and follow-up paths pass;
- two-instance isolation passes;
- the rollback baseline remains unchanged and available.
