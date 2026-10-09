# WordPress production integration sources

The canonical sources for The Guide frontend are:

- HTML and markup wrapper: `wordpress/the-guide-frontend.html`
- JavaScript controller: `wordpress/the-guide-frontend.js`
- Production JS asset: `https://geralddaquila.com/wp-content/uploads/2026/08/living-archive-guide-v489.12.js`
- Production Woody snippet: **#76926**, “USE Outer Courtyard Search”
- Public entry page: `https://geralddaquila.com/the-guide/`, WordPress page **#76925**
- Current deployed frontend build: **v489.12**

## Why JavaScript is external

WordPress transformed inline JavaScript operators such as `&&` into HTML entities inside the rendered script body (for example, `&#038;&#038;`). The browser then rejected the entire script before the Guide submission controller could install. The controller is now served as a standalone JavaScript asset with MIME type `application/javascript`, outside the page-content filter path. LiteSpeed optimization/defer rewriting is excluded for the external controller as well.

## Change protocol

1. Make a full-file replacement in `wordpress/the-guide-frontend.js` and advance its build marker.
2. Run `python QA/WORDPRESS_GUIDE_FRONTEND_QA.py`, `node tests/e2e/check-guide-source-syntax.cjs`, and the backend contract checks.
3. Upload the exact JavaScript file to WordPress media and verify its HTTP status, MIME type, byte length, and exact content.
4. Update the HTML wrapper to reference the versioned external asset; deploy that wrapper to Woody snippet #76926.
5. Re-read the live snippet and verify its source matches the repository wrapper.
6. Update the page #76925 build marker, purge LiteSpeed cache, and verify the live browser controller and recommendation link.
7. Keep one active Guide runtime, one submission owner, and one authoritative recommendation renderer. Do not add a second controller as a fallback.

## Release gates

- Static source QA checks single-owner submission, canonical recommendation URL validation, and no browser-manufactured fallback answer.
- Browser contract E2E verifies one request, preserved answer paragraphs, and visible clickable recommendation.
- Live API E2E verifies a real POST to the production backend returns answer text and recommendation metadata and that the browser displays the same canonical URL.

GitHub does not automatically deploy its repository source to WordPress. Media upload, Woody activation, page marker update, cache purge, and live verification are explicit deployment steps.
