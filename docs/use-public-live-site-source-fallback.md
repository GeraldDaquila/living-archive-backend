# USE public live-site source fallback

The internal canonical corpus and Constitutional Register remain the primary
authority. `PublicLivingArchiveClient` is a bounded, anonymous WordPress REST
adapter intended only as a fallback after USE's existing evidence gate reports
that the internal result set cannot support the current question.

## Security boundary

- Uses only anonymous REST search and individual public post/page views.
- Accepts only `publish` posts/pages on the exact HTTPS `geralddaquila.com` host.
- Rejects WordPress password-protected content, non-public post types, and known
  Guardian/Stewardship protected URL families.
- Rejects documents containing recognized membership/access-control shortcodes
  rather than risking extraction of enclosed protected material.
- Removes Gutenberg block comments, shortcode tokens, and non-content HTML
  chrome; scripts, styles, navigation, headers, footers, forms, and noscript
  content are excluded.
- Limits results, passage length, response bytes, request timeout, and cache TTL.
- Logs only outcome/count or exception type; never logs query text or passages.

The live site is a partial public reflection of the wider archive. It does not
replace private T4/Guardian materials, and this adapter must never be used to
retrieve those materials. Unknown access-control markup is a reason to fail
closed and extend the deny rules, not to assume content is public.

## Evidence and evaluation

Each returned resource includes canonical URL, title, WordPress ID, source
modified time, retrieval time, and the normalized passage. These are answer-
grounding provenance fields only. They are not paired LLM/deterministic captures,
held-out benchmark evidence, application observations, or outcome measurements.
No adaptive-quality claim may be inferred from successful source retrieval.

## Integration status

This module is an isolated adapter increment. It must be integrated behind the
existing internal evidence gate and covered by USE query-level tests before it
can be treated as active runtime behavior.
