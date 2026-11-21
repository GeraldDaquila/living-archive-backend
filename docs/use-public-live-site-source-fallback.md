# USE public live-site source fallback

The internal canonical corpus and Constitutional Register remain the primary
authority. `PublicLivingArchiveClient` is a bounded, anonymous fallback
adapter intended only after USE's existing evidence gate reports that the
internal result set cannot support the current question.

## Retrieval path

1. Search the anonymous WordPress REST search endpoint for published search
   candidates. The adapter accepts only the standard `post` and `page`
   subtypes; other post types are not eligible by default.
2. Fetch candidate content through the site's dedicated
   `/wp-json/living-archive/v1/canonical-evidence/{id}` endpoint, provided by
   the active Living Archive Canonical Evidence Bridge plugin.
3. The bridge checks `post_status=publish`, native WordPress password
   protection, and `is_post_type_viewable()`. It reads stored content without
   running `the_content`, theme filters, or shortcodes, then strips HTML and
   returns bounded text plus title, permalink, ID, modified time, and source
   type.
4. The adapter independently validates source type, ID, exact HTTPS host,
   protected URL families, minimum content length, and residual known access
   shortcodes before admitting a passage.

## Security boundary

- Uses anonymous read-only endpoints; no Cowboy MCP credentials or privileged
  admin connection is part of runtime retrieval.
- Accepts only published, viewable, standard post/page candidates and the
  dedicated canonical evidence bridge response.
- Rejects native password-protected resources (the bridge returns 404),
  non-public post types, and known Guardian/Stewardship protected URL families.
- Never executes WordPress shortcodes or theme/plugin content filters.
- Rejects residual known membership/access-control shortcode tokens rather
  than risking extraction of enclosed protected material.
- Limits results, passage length, response bytes, request timeout, and cache TTL.
- Logs only outcome/count or exception type; never logs query text or passages.

The site bridge's native password check is authoritative for WordPress
password-protected posts. This adapter is not a general-purpose authorization
oracle for arbitrary future plugin-level gates. If a new protection mechanism
is introduced, its route/path or content marker must be explicitly reviewed
before the adapter is allowed to consume it. Unknown access-control markup is
a reason to fail closed and extend the deny rules, not to assume content is
public.

The live site is only a partial public reflection of the wider archive. It
does not replace private T4/Guardian materials and must never be used to
retrieve them.

## Evidence and evaluation

Each returned resource includes canonical URL, title, WordPress ID, source
modified time, retrieval time, normalized passage, and an explicit marker that
the passage is untrusted external evidence rather than an instruction source.
These fields support visitor answer grounding only. They are not paired
LLM/deterministic captures, held-out benchmark evidence, application
observations, or outcome measurements. No adaptive-quality claim may be
inferred from successful source retrieval.

## Integration status

This module is an isolated adapter increment. It must be integrated behind the
existing internal evidence gate and covered by USE query-level tests before it
can be treated as active runtime behavior.
