# The Guide — Copy/Paste Page-Type Templates

Status: design-ready templates, NOT approved for production paste until the shared Woody snippet passes its single-instance live E2E gate.

## Governing rule

Use one canonical Guide implementation (Woody Snippet ID 76926) across page types. Do not create three independent JavaScript controllers or fork the form's internal markup. The page type changes the surrounding invitation and context, not the underlying Guide behavior.

The template blocks below are intended to be pasted into a WordPress Shortcode block (or the site's equivalent shortcode-capable block). Each template includes exactly one Guide shortcode. Do not paste the full controller or duplicate the form markup into the page.

## 1. Landing page — broad entry

Use on the main Guide landing page when the visitor may not yet know which subject or pathway they need.

### Copy/paste block

```text
Ask a question, follow a curiosity, or find what you need.

[wbcr_snippet id="76926"]
```

### Intended behavior

- Broad, open invitation.
- No assumed subject or prior knowledge.
- Guide determines the appropriate next step through the existing USE routing and specialist contracts.

## 2. Hub page — topic-oriented entry

Use on a hub page where the visitor is already exploring a defined subject. Replace the bracketed phrase with the actual hub topic before pasting.

### Copy/paste block

```text
Explore this hub more deeply.

Have a question about [HUB TOPIC], or want help finding where to begin? Ask below.

[wbcr_snippet id="76926"]
```

### Intended behavior

- The surrounding copy makes the hub context clear.
- Do not silently force the hub topic into the visitor's query.
- Do not add a separate controller or rewrite specialist-routing behavior for this page.

## 3. Cornerstone page — depth-oriented entry

Use on a cornerstone page after the main argument or near the concluding navigation area. Replace the bracketed phrase with the cornerstone's central question or theme.

### Copy/paste block

```text
Continue exploring this question.

If you want to connect this essay to the wider Living Archive, ask a question about [CORNERSTONE THEME] or find a useful next step below.

[wbcr_snippet id="76926"]
```

### Intended behavior

- The invitation connects the essay to further exploration without restating or replacing its thesis.
- Keep the user's question sovereign: do not prefill a query or force a destination.
- The Guide retains its existing canonical retrieval, response, and specialist handoff behavior.

## Shared implementation requirements

1. One canonical shortcode/snippet and one shared controller; page types do not get independent code forks.
2. Exactly one Guide instance per page in the initial rollout.
3. The snippet owns its own form submission and response lifecycle.
4. Keep page-specific text outside the shared snippet unless a future explicit configuration contract is added.
5. Do not invent shortcode attributes such as `variant="hub"` or `context="cornerstone"`; no such API has been verified.
6. The snippet must pass single-instance submission, one-request, visible-substantive-answer, follow-up, and specialist-handoff checks before any of these blocks are used in production.
7. Before broad rollout, verify the shortcode on one test hub and one test cornerstone; check layout, caching, accessibility, and that the shared Guide behaves exactly like the restored Custom HTML baseline.

## Current rollout state

- The restored Custom HTML baseline on page 76925 is the known-good visual/behavioral reference.
- Woody Snippet 76926 is still a migration candidate; its live submission has not yet passed browser E2E.
- These are copy/paste page-shell templates, not a claim that the shortcode is production-ready.
