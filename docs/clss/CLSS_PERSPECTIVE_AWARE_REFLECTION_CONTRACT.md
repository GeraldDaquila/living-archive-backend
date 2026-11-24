# CLSS Perspective-Aware Reflection — Implementation Contract

Status: proposed acceptance specification; not yet implemented in WordPress.
Scope: CLSS only. This work must not change USE, The Guide, `use_core.py`, Render services, embeddings, provider configuration, or any production USE build.

## 1. Entry choice

Before Question 1, the visitor must choose one explicit mode:

- **Reflect on my own leadership** (`self`)
- **Reflect on another person's leadership** (`third_party`)

Explain the distinction in plain language. Do not preselect a mode. The visitor can go back and change the mode before starting; changing mode after answers exist must ask whether to clear the answers, never silently reinterpret them.

## 2. Preserve the nine-question baseline

The current nine question strings are protected pending explicit approval. Do not silently rewrite or replace them. The existing baseline is third-person framed and therefore cannot simply be displayed unchanged in self mode. Until wording is approved, treat the self-mode wording as a pending editorial decision and do not claim that the interface fully supports self-assessment.

The two modes must have equivalent coverage across the same five dimensions:
1. intention and responsibility;
2. decisions and actions;
3. relational and systemic effects;
4. recognition, correction, and response to feedback;
5. bounded stewardship, consent, authority, and review.

## 3. Perspective-specific framing

### Self mode

- Address the visitor as “you” and invite first-person concrete examples.
- Separate what I did, what others experienced/reported, what I infer, and what remains unknown.
- Encourage accountability without shaming or self-exoneration.
- Invite alternative explanations and impact that may differ from intent.
- Never infer that uncertainty or an unanswered question means failure.

### Third-party mode

- Refer to the person being considered without asserting access to their motives or inner character.
- Separate direct observation, documented outcomes, testimony/reports, inference, conflicting accounts, and unknowns.
- Treat a single anecdote as limited evidence; consequential claims require proportionate corroboration.
- Include effects on other people and system conditions, not only individual traits.
- Do not turn the result into a hiring recommendation, suitability score, diagnosis, or moral verdict.

## 4. Evidence and result behavior

The result must:
- preserve links from each claim to the specific answer(s) that support it;
- distinguish observed, reported, inference, unknown, and tension/conflict;
- state uncertainty and at least one plausible alternative reading where interpretation is offered;
- avoid converting a blank answer into negative evidence;
- distinguish intention from action and impact;
- identify missing or contradictory evidence explicitly;
- offer bounded next steps that gather evidence or clarify conditions, not prescribe a verdict.

The summary should first reflect the visitor's evidence, then state what is supported, uncertain, conflicting, and still unknown. It must not manufacture a narrative when evidence is sparse.

## 5. Doorway/resource selection

Do not always display the same three resources. A canonical doorway may be recommended only when:
- a concrete unresolved need is grounded in the answers;
- the resource is in the approved canonical registry and its exact title/URL match;
- the reason for the doorway is explained in one sentence;
- no recommendation is preferable when evidence is too sparse or the need is not established.

Never fabricate a destination or infer suitability from the choice of doorway.

## 6. Privacy and session behavior

Retain the current stated boundary: answers stay in the current page session and are not submitted to a server. Do not add analytics, API calls, persistence, or transmission of answers without separate explicit approval. A mode change must not transmit answers. Print must be user-initiated and should print the result only.

## 7. Acceptance tests required before publication

1. Self mode uses first-person/self-accountability framing throughout all nine prompts and result labels.
2. Third-party mode uses evidence-bounded third-party framing throughout.
3. Switching mode after entering answers never silently transfers/reinterprets them.
4. All answers blank → summary identifies insufficient evidence, no verdict, no forced doorway.
5. One brief anecdote → limited confidence and a corroboration step, no character claim.
6. Intention differs from impact → both remain visible; neither cancels the other.
7. Conflicting reports → conflict remains explicit; system does not choose a winner without evidence.
8. Unsupported motive claim → labeled inference, alternatives offered, motive not stated as fact.
9. Systemic constraints plausibly explain behavior → consider context rather than attributing everything to character.
10. Potential retaliation/suppressed dissent → describe the risk carefully and suggest safe, proportionate evidence gathering; no unsupported accusation.
11. Blank answers remain unknown, not adverse evidence.
12. Resource recommendation is answer-grounded and registry-validated, or absent.
13. Invalid/unregistered URL cannot render as a doorway.
14. Print action prints the result only and leaves the live page usable.
15. No request containing answer content is sent to any server; verify with browser network inspection.
16. Keyboard navigation, visible focus, labels, and screen-reader announcements work for mode selection and question transitions.
17. Existing shortcode renders only where intentionally placed; no global injection or duplicate IDs.

## 8. Change control

- First deliver the question wording and mode-specific result examples for review.
- Preserve the nine-question baseline until wording is explicitly approved.
- Then prepare a reviewed full-file replacement of `wp-content/plugins/clss-guided-reflection-prototype/clss-guided-reflection-prototype.php` via Cowboy MCP, with a backup/checkpoint and PHP syntax validation.
- Do not edit or activate a Woody Snippet as a substitute for the shortcode plugin unless the target architecture is explicitly chosen.
- Do not publish the private draft until all acceptance tests are actually run and pass.
- Deterministic schema tests do not prove semantic quality; scenario adjudication is required.
