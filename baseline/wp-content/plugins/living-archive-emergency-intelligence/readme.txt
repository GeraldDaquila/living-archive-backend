=== Living Archive Emergency Intelligence ===

Version: 0.1.1

Purpose:
Maintain a locally verified, independently updateable emergency-resource intelligence layer for Living Archive instruments.

Important:
- This plugin is standalone.
- It does not modify or require the Human Relational Navigator plugin.
- HRN can invoke living_archive_emergency_resolve() after its Safety Fractal determines the service need.
- The emergency path uses the local verified registry and never waits for an update.
- Registry refresh is attempted only when the six-hour freshness window is due.
- A downloaded registry is validated before activation.
- Cryptographic signature enforcement is intentionally disabled until a canonical registry public key is provisioned.

Initial prototype countries:
Philippines, United States, Germany, China, United Kingdom.

Current registry does not include China's regionally reported 999 ambulance number.

The plugin is a prototype and should not be treated as a substitute for official emergency-service verification.
