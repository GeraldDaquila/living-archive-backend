# FSD WordPress Integration Bundle — Release Manifest

- Bundle version: 0.2.3
- Captured from live WordPress through Cowboy MCP: 2026-11-04
- Source of authority for WordPress changes: Cowboy MCP
- Branch: feat/fsd-two-quantum-mvp
- Backend candidate: fc3986d00434dbb2ec0560380c217ed6e21baf7a (before integration-bundle commits)
- PHP proxy active on WordPress: 0.2.3
- Asset cache-busting version: 0.2.3
- Feature flags: disabled
- Staging page ID: 80594 (draft)
- Public page ID: 76640 (unchanged)
- Candidate backend route: not deployed on primary or mirror
- Credential material: deliberately excluded

## Source checksums (GitHub Git blob SHA-1)

| File | Blob SHA-1 | Bytes |
|---|---|---:|
| living-archive-fsd-proxy.php | 03945cc5641a913e36577656c0c3b4f08944c270 | 10243 |
| assets/fsd-app.js | 58183c5981f3867276027c67a2f9d44b5fc51cd1 | 15667 |
| assets/fsd-app.css | f15a62333d0860ecb85cd1794e53dd2126574c90 | 2739 |
| README.md | b34d41abc07f8ca8ddfaba09af3078b6d23deb0f | 1299 |

The blob IDs are Git's content-addressed SHA-1 identifiers, not SHA-256 digests. They allow exact source retrieval and comparison within this repository. This manifest is an integration provenance record, not a cryptographic supply-chain attestation.

## Verification limits

This bundle and its static integration simulation do not prove:
- host-side protected credential configuration or coordinated key rotation;
- live WordPress-to-Render authenticated POST success;
- provider processing/retention approval;
- authenticated browser rendering of the private draft;
- independent editorial/release approval.

Do not enable either feature flag or publish the staging page until those gates are closed.
