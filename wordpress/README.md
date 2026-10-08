# WordPress production integration sources

The canonical source for The Guide frontend is `wordpress/the-guide-frontend.html`. Production destination: Woody snippet #76926, “USE Outer Courtyard Search”. Public entry page: `https://geralddaquila.com/the-guide/` (WordPress page #76925). Current snapshot build: v489.09.

## Change protocol

1. Change the repository source first using a full-file replacement.
2. Run `python QA/WORDPRESS_GUIDE_FRONTEND_QA.py` and the backend contract checks.
3. Deploy that exact source to Woody snippet #76926. Never create a second active Guide runtime.
4. Re-read the live snippet and verify the build, single submission owner, response contract, and canonical URL validation.
5. Update the page's build marker, purge LiteSpeed cache, and verify the public page.
6. Reconcile any difference between repository source and live Woody code before making another change.

## Invariants

- One active Guide frontend runtime.
- One submission owner for `#archive-search-form`.
- One response contract carrying answer text and structured recommendation metadata.
- One authoritative recommendation renderer.
- No browser-manufactured fallback answer when backend composition fails.

This repository source is the source-of-truth step; GitHub does not automatically deploy it to WordPress. Deployment remains explicit and must be verified against the live snippet.
