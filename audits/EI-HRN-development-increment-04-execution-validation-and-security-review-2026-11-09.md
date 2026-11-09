# EI–HRN Development Increment 04 — Execution Validation and Security Review
Date: 2026-11-09
Branch: `dev/ei-security-and-hrn-adapter-20261109`
Successful validation commit: `e2b1fca23a4c19382cbed7a633db610c62a300a5`
Successful GitHub Actions run: [42586027014](https://github.com/GeraldDaquila/living-archive-backend/actions/runs/42586027014)

## Result
The EI–HRN adapter validation workflow completed successfully. All workflow steps passed:
- PHP syntax validation across the HRN and EI plugin PHP files.
- JavaScript syntax validation for the HRN frontend.
- Static location-only boundary assertions.
- Isolated execution of the actual HRN `resource_location_handler`.
- EI–HRN location-only regression tests (pytest).

## Handler behaviors exercised
- Resource-only operation marker is returned.
- Existing safety stage, question and prompt are preserved exactly.
- Equivalent official emergency numbers are both retained.
- EI is queried for the three intended resource categories.
- EI registry version is surfaced.
- EI exception/outage retains the HRN legacy resource path without changing the safety stage or question.
- An unrecognized country fails closed with a client-correctable location error.
- An invalid safety stage fails closed.
- The public route is registered explicitly.

## Test harness scope and limitations
The PHP test loads the actual HRN plugin class and executes its handler under minimal WordPress stubs. The repository checkout does not contain the production canonical-retriever include, so the harness creates a temporary empty test-only include solely to satisfy plugin initialization, then removes it. The tested handler does not invoke canonical retrieval.
This is not a full WordPress bootstrap, production plugin runtime, live EI registry integration, browser test, or end-to-end visitor journey. It does not certify WordPress hook ordering, actual REST serialization, reverse-proxy behavior, browser state, or hosting-level controls.


## Additional read-only WordPress cache inspection
A read-only inspection through the site's authorized Cowboy MCP administration path reported LiteSpeed Cache 7.9.3. Its `cache-rest` setting is enabled with a 3600-second REST cache TTL. This is not evidence that POST requests to these resource endpoints are cached; it does mean endpoint-specific cache behavior must be checked rather than assumed.
The LiteSpeed object-cache feature flag is off in the returned settings, despite localhost/Memcached connection fields being populated. Therefore the rate-limit design must not assume a functioning distributed object cache or atomic shared counter. Confirm actual runtime behavior before choosing a counter store. No settings were changed.

## Security review — open findings
1. The HRN resource-only route is public (`permission_callback => __return_true`). This is intentional for crisis accessibility, but the route currently has no explicit application-level rate limiting or abuse telemetry.
2. The EI `/resolve` and `/resolve-bundle` routes are also public. Bundle validation limits the number of service categories to 10, but request-size controls, rate limiting and abuse telemetry need a separate review.
3. Do not trust arbitrary client-supplied forwarding headers as source IP evidence. Before implementing IP-based limits, establish the actual trusted proxy/CDN chain and the WordPress hosting environment's canonical client-IP mechanism.
4. Do not add login, CAPTCHA, or other friction that can block a person seeking emergency help. Prefer low-friction abuse controls, bounded request processing, short-lived privacy-minimizing counters, and monitoring.
5. No new security control is implemented by this increment. Rate limiting remains an open item pending confirmation of hosting/proxy topology and safe storage behavior.

## Protected invariants
The HRN risk classifier, safety answer classifier, transition logic, safety response logic and normal conversation handler remain outside the resource-only adapter path. No production WordPress files were changed. No PR, merge to main, or production deployment was performed.

## Next gates
1. Establish trusted client-IP/proxy topology and the availability/behavior of WordPress object cache or transient storage.
2. Design and test non-blocking abuse controls with emergency-access exceptions and bounded request sizes.
3. Build a genuine staging WordPress integration test with both plugins loaded in production-like order.
4. Run browser-level E2E tests covering location-only submission, exact safety-state preservation, EI outage, unsupported country, and normal HRN conversation isolation.
5. Expand EI resource coverage only with independently verified sources and review dates.
