# WordPress Runtime Inventory — 2026-10-15

**Method:** Read-only Cowboy MCP `wp_list_plugins(status=active)`.  
**Mutation:** None. No plugin was activated, deactivated, updated, or deleted.

## Relevant active plugins

| Component | Plugin file | Live version | State | Recovery implication |
|---|---|---:|---|---|
| Cowboy MCP | `cowboy-mcp/cowboy-mcp.php` | 1.7.3 | Active | Sole WordPress administration path |
| HRN | `human-relational-navigator/human-relational-navigator.php` | 0.5.330 | Active | Exact live source must be recovered before repair |
| HRN rollback capture | `hrn-rollback-capture/hrn-rollback-capture.php` | 1.0.0 | Active | Temporary safety artifact; documents a private v0.5.310 copy, not a current rollback target |
| HRN command boundary adapter | `hrn-command-boundary-adapter/hrn-command-boundary-adapter.php` | 1.3.0 | Active | Must be included in HRN round-trip E2E |
| HRN latency guard | `living-archive-hrn-latency-guard/living-archive-hrn-latency-guard.php` | 1.2.0 | Active | Provider timeout/circuit boundary; inspect behavior without changing frozen HRN voice |
| HRN perception overlay | `living-archive-hrn-perception-overlay/living-archive-hrn-perception-overlay.php` | 0.1.1 | Active | Must be tested only on its intended specialist path and must not affect General Purpose USE |
| Living Archive Navigator (LAN) | `public-living-archive-navigator-v0.3.3-DUPLICATE-TITLE-GUARD-COLOR-NEUTRAL/living-archive-navigator.php` | 0.3.3 | Active | Live subject-relevance defect remains open |
| Mini-USE Catalogue bridge | `mini-use/mini-use.php` | 0.2.39 | Active | WordPress bridge needs canonical-link and error-contract E2E |
| Living Archive – Cowboy Authority | `living-archive-cowboy-authority/living-archive-cowboy-authority.php` | 1.1.0 | Active | Maintains Cowboy MCP as sole agent authority |
| Living Archive Atlas Finder | `living-archive-atlas-finder-v0.4.7/living-archive-atlas-finder.php` | 0.4.8 | Active | Preserve as a separate instrument; do not conflate with LAN |
| Living Archive Emergency Intelligence | `living-archive-emergency-intelligence/living-archive-emergency-intelligence.php` | 0.1.2 | Active | Include its own safety/resource route in the broader regression gate |

## Interpretation and controls

1. Plugin versions above are current observations from the active plugin listing at the time recorded. They are not source hashes or proof of successful visitor journeys.
2. The HRN overlay, latency guard, and command-boundary adapter are distinct layers. A full HRN test must identify which layer handled each step and ensure no overlay affects the frozen General Purpose path.
3. The rollback-capture plugin remains active during recovery. Do not use its v0.5.310 artifact to overwrite v0.5.330. Reassess whether the temporary plugin should be retired only after an authoritative v0.5.330 source snapshot and verified rollback plan exist.
4. Do not make speculative plugin cleanup during recovery. The Guide, LAN, HRN, Catalogue bridge, Atlas Finder, Emergency Intelligence, and Cowboy authority have distinct responsibilities.
5. WPVibe is not present in the relevant active-plugin results. Cowboy MCP remains active and is the sole WordPress administration path.

## Required integration tests

- **General Purpose isolation:** run the frozen General Purpose gold-standard fixture with the HRN perception overlay present; confirm no HRN framing, prompt, or output leaks into the General Purpose response.
- **HRN entry and completion:** natural relational entry → HRN composition → question completion → multi-turn progression → explicit closure → return to Guide → independent canonical recommendation.
- **LAN relevance:** institutional-responsibility query with hard subject-fit gates; no unrelated padding.
- **Catalogue bridge:** WordPress endpoint → Catalogue → verified asset ID/title/URL; malformed or unavailable results fail boundedly.
- **Safety/resource routing:** verify emergency-intelligence path independently, without treating a registration record as proof of a completed journey.
- **Admin authority:** verify only Cowboy MCP is used for WordPress administration; no WPVibe dependency is introduced.

## Evidence links

- HRN composition blocker: https://github.com/GeraldDaquila/living-archive-backend/issues/534
- Ecosystem recovery mandate: https://github.com/GeraldDaquila/living-archive-backend/issues/638
- Contract registry draft: https://github.com/GeraldDaquila/living-archive-backend/pull/639
