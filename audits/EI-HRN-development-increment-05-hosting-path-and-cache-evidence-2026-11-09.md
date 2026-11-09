# EI–HRN Development Increment 05: Hosting Path and Cache Evidence

Date: 2026-11-09  
Branch: `dev/ei-security-and-hrn-adapter-20261109`  
Scope: read-only production hosting and route inspection. No production writes, no POST resource-resolution tests, no deployment.

## Executive finding

The production WordPress site is hosted on WordPress.com infrastructure. Read-only diagnostics and response headers identify Nginx, WordPress.com hosting, Atomic edge infrastructure, and Batcache. Cloudflare was not detected by the Cowboy MCP connection doctor. This replaces the previous uncertainty about the hosting/proxy family, but it does not yet identify the complete trusted client-IP forwarding chain or prove a supported host-level rate-limit control.

## Evidence collected

### Runtime
- Site: `https://geralddaquila.com`
- WordPress: 7.1.4
- PHP: 8.4.27
- Server software reported by connection doctor: Nginx
- WordPress.com host marker: `host-header: WordPress.com`
- Atomic edge marker: `x-ac: ... _atomic_dca ...`
- Homepage response included `x-nananana: Batcache-Hit`.
- Homepage response included `server-timing: a8c-cdn, dc;desc=dca, cache;...`.
- Connection doctor result: 14 pass, 0 warnings, 0 failures, 1 skipped; Cloudflare detection skipped because Cloudflare was not detected.

### Cache response evidence
- Homepage HEAD response: HTTP 200; `cache-control: max-age=286, must-revalidate`; Batcache marker present; `x-ac` reported Atomic cache MISS for that request.
- EI status GET response: HTTP 200; `x-litespeed-cache-control: public,max-age=3600`; `x-litespeed-tag: ...REST...`; `x-ac` reported Atomic cache STALE. This is a GET status endpoint and may be cacheable.
- EI resolve OPTIONS response: HTTP 200; `allow: POST`; `x-litespeed-cache-control: no-cache`; `cache-control: no-cache, must-revalidate, max-age=0, no-store, private`; `x-ac` reported Atomic cache BYPASS.
- OPTIONS is not a POST request. Therefore these observations strongly indicate that the POST route's preflight/OPTIONS response is bypassed, but they do not conclusively prove the caching behavior of an actual POST request. No POST request was sent to production.

### Live route inventory
The live emergency namespace currently exposes:
- `GET /wp-json/living-archive/emergency/v1/status`
- `POST /wp-json/living-archive/emergency/v1/resolve`

The new development-only routes are not present in production:
- `POST /wp-json/living-archive/emergency/v1/resolve-bundle`
- `POST /wp-json/living-archive/v1/emergency-resources`

The production EI status response still reports plugin version `0.1.2`, registry `2026.10.13.001`, and update status `not_configured` because the canonical registry endpoint is not configured.

## Interpretation and limits

1. WordPress.com hosting and Atomic edge infrastructure are now evidenced. Cloudflare should not be assumed.
2. Batcache is a page/HTML cache, distinct from the global edge cache and object cache. The observed homepage Batcache hit does not establish that REST POST responses are cached.
3. The EI status GET response carried REST cache headers and an Atomic STALE marker. It must be treated as potentially cacheable; status freshness should not be inferred from HTTP 200 alone.
4. The EI resolve OPTIONS response was marked no-cache and Atomic BYPASS. This is not a substitute for a controlled POST behavior test.
5. No trustworthy client-IP forwarding chain, origin request-IP variable, or provider-supported rate-limiting interface has yet been established. Do not implement IP throttling using arbitrary client-supplied forwarding headers.
6. No WordPress cache settings, plugins, files, routes, or production code were changed.

## Next gates

1. Establish the authoritative WordPress.com-supported client IP mechanism and trusted proxy chain, ideally from host documentation/support or a documented platform API. Do not probe by accepting arbitrary `X-Forwarded-For` values.
2. Confirm the cache behavior of the EI and HRN POST routes in a controlled staging environment. Avoid POST probes against production until a bounded, harmless test case is explicitly designed and authorized.
3. Determine whether WordPress.com provides a suitable edge/WAF abuse-control feature for this hosting plan, and whether it can exempt/allow crisis-resource access without login or CAPTCHA barriers.
4. If host-level rate limiting is unavailable, design bounded request controls only after confirming a shared atomic storage primitive and trusted request identity. Do not assume WordPress transients or LiteSpeed object cache are atomic/distributed.
5. Continue staging integration and browser E2E on the isolated development branch. No merge, PR, or production deployment is authorized by this audit.

## Release status

This is an evidence-gathering increment, not a release gate pass. EI–HRN remains development-only and is not production-ready. HRN deterministic safety boundaries remain protected.
