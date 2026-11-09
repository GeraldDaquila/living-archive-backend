# EI–HRN Development Increment 06: Platform WAF Review and Regression Expansion

Date: 2026-11-09  
Branch: `dev/ei-security-and-hrn-adapter-20261109`  
Scope: documentation of WordPress.com security capabilities and added isolated handler regression tests. No production writes, no live POST probes, no deployment.

## 1. Platform WAF findings

Current WordPress.com documentation states:
- WordPress.com sites receive platform-level WAF and DDoS protection.
- Eligible plugin-enabled plans expose security settings, including brute-force login protection and an allowlist for specific IP addresses.
- WordPress.com documents no custom inbound firewall rules for customer sites.
- Defensive Mode presents a browser challenge and is a poor routine safeguard for crisis-resource flows because it can interrupt access.

Sources:
- https://wordpress.com/support/hosting-configuration/
- https://wordpress.com/support/firewall-rules/
- https://wordpress.com/support/defensive-mode/
- https://wordpress.com/support/security/

Interpretation:
- Platform WAF is a baseline security layer, not proof that EI/HRN endpoints have endpoint-specific quotas or abuse telemetry.
- Public documentation reviewed does not establish a customer-configurable path-specific rate limit for arbitrary REST routes.
- Site plan eligibility and actual security settings were not confirmed through the WordPress site runtime; Cowboy site info does not expose the hosting plan/security dashboard state.
- Do not enable Defensive Mode as routine mitigation for EI/HRN. Do not add allowlist-only access to public emergency resources.
- Ask WordPress.com support whether endpoint-specific rate limiting, request logs, trusted client IP attribution, or path exemptions are available for this site and plan before designing application-level controls.

## 2. Regression expansion

Extended `tests/php/test_hrn_resource_location_handler.php` to cover:
- Deduplication when the same emergency phone number is returned by multiple EI service categories.
- EI no-match behavior retaining HRN continuity resources when available.
- Accurate legacy-fallback provenance when EI has no eligible match.
- Preservation of the active HRN stage and question under EI no-match.

Successful workflow:
- Run ID: `42587160430`
- Commit: `fce6583f65f0fa75fb0f624591c8bb1d86d21507`
- URL: https://github.com/GeraldDaquila/living-archive-backend/actions/runs/42587160430
- Result: success.
- Passed: PHP syntax, JavaScript syntax, location-only boundary assertions, isolated HRN handler execution, and EI-HRN source-contract regression tests.

This remains a source-level and isolated PHP execution harness. It is not a full WordPress bootstrap, staging integration, browser E2E, or production runtime test.

## 3. Security decisions retained

- HRN remains the sole owner of risk classification, safety state, transitions, and intervention progression.
- EI remains a location/resource lookup service only.
- No login or CAPTCHA barriers are introduced for crisis-resource routes.
- No IP-based limiter is implemented until trusted proxy/client identity and shared atomic storage are confirmed.
- No assumptions are made about WordPress transients or the LiteSpeed object-cache feature.
- No production POST test was performed.
- No WordPress settings or files were changed.

## 4. Next actions

1. Obtain WordPress.com support confirmation for trusted origin client-IP attribution, endpoint/path-level rate controls, and available request telemetry for this site and plan.
2. Identify an existing safe staging WordPress instance or an approved isolated staging route. Do not create billable infrastructure or deploy without authorization.
3. Perform full WP bootstrap and browser E2E against staging, including EI success/no-match/outage, location-only submission, ordinary HRN conversation, and exact safety-stage preservation.
4. Independently verify emergency contact data before any registry expansion or production promotion.
5. Complete full pre-release gates only after staging integration and browser tests pass.

## Release status

Development only; not release-ready. No PR, merge, main-branch update, or production deployment.
