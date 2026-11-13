# LAN live-source recovery snapshot

This directory is an archival recovery snapshot of selected source files read from the live WordPress installation on 2026-10-15. It is **not a deployable plugin package** and must not be installed as-is.

## Captured
- `living-archive-navigator.php` — live plugin entrypoint, version 0.3.3
- `includes/class-lan-engine.php` — complete live engine source (51,982 characters)
- `data/relationships.json` — live relationship file, which declares `not_available_from_supplied_exports` and has an empty relationship list

## Still missing / blocked
- `data/corpus-runtime.json` — live reader refuses to return this file (reported as 2 MB)
- `data/retrieval-index.json` — live reader refuses to return this file (reported as 4 MB)
- Any corpus/index-generation script, source export, and reproducible build instructions
- A full inventory of the plugin directory; the current WordPress directory-listing tool errors with `SplFileInfo::isDot()`
- Local runnable tests against the actual corpus and index

## Safety and authority
- This snapshot is for source recovery and code review only.
- It does not change WordPress production.
- Do not create substitute corpus/index data or fabricate semantic relationships.
- Before modifying live LAN, recover the authoritative corpus and generation pipeline, add subject-fidelity regression tests, review a complete package, and run live endpoint plus visitor-facing E2E.
- The frozen General Purpose USE gold-standard answer/composition and protected `use_core.py` are outside this work and must remain unchanged.

## Confirmed defect to repair
The live engine's `deterministic_plan()` assigns broad experience/pattern/structure regex bonuses but has no hard subject-relevance gate. This can select unrelated items for specific resource-discovery questions. A future fix must prefer fewer well-grounded destinations or transparently report insufficient relevant sources over padding the path with unrelated content.
