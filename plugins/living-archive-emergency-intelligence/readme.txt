=== Living Archive Emergency Intelligence ===

Version: 0.1.3

Purpose:
Provide deterministic, provenance-verified emergency-resource selection for Living Archive instruments.

Architecture:
- Standalone PHP subsystem with its own registry, location resolver, selector, engine, presenter, and REST interface.
- No dependency on HRN and no HRN visitor-routing or session integration.
- The selector emits callable telephone actions only for active resources with current, resource-mapped verification evidence.
- Explicit current user location statements take precedence over browser, IP, timezone, and locale inference.
- Invalid local registries fail closed; stale cached registry data is discarded when a forced reload fails.

Registry:
- Schema version 0.2; current registry version 2026.11.09.001.
- Current data covers five countries: Philippines, United States, Germany, China, and United Kingdom.
- This is not yet the ten-country parity target.
- HTTPS source URLs and resource mappings are required structurally; source meaning and coverage still require human editorial verification.

Security:
- Remote registry updates are disabled.
- No remote endpoint is contacted.
- Re-enablement requires cryptographic signature verification, trusted-key provisioning and rotation, replay protection, and positive/negative tests.
- A content hash alone is not publisher authentication.

Release status:
- Development branch only.
- Standalone PHP/registry validation has passed.
- Full country-parity, contextual-selection, resource-alternative, WordPress integration, and browser E2E gates remain outstanding.
- This plugin is not a substitute for contacting official emergency services.
