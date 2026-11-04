# Living Archive FSD Proxy — WordPress integration

Release bundle version: 0.2.3

This directory is the source-controlled release copy of the WordPress proxy and its staging-only browser assets. The production plugin files were read through Cowboy MCP, the sole WordPress administration authority, on 2026-11-04. The PHP proxy includes the route-scoped no-store response filter and pins the CSS/JS asset cache-busting version to 0.2.3.

## Boundaries
- The REST route is registered only when BOTH `la_fsd_proxy_enabled` and `la_fsd_proxy_staging_enabled` are true.
- Browser assets enqueue only on staging page ID 80594.
- The proxy delegates the shared credential lookup to `la_provider_bank_shared_secret()`; no credential is included in this bundle.
- The endpoint forwards to the existing primary and mirror USE services only.
- The UI describes one respondent-reported episode; Archive references are conceptual context, not corroboration.
- The bundle is not permission to enable flags or publish the staging page.

## Release state at capture
- WordPress proxy plugin: active, v0.2.3.
- Staging page: private draft.
- Public page: unchanged.
- Primary/mirror FSD candidate route: not deployed.
- Feature flags: disabled.
- This bundle does not contain host credentials or provider API keys.
