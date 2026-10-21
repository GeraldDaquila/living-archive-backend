# Source Recovery Search Log — 2026-10-15

**Purpose:** Prevent repeated exploratory searches and distinguish repository history from exact live production source. This log records targeted read-only GitHub searches; it is not proof that no copy exists anywhere outside the searched repository/branch index.

## HRN source search

### Searches performed
- Searched commits in `GeraldDaquila/living-archive-backend` for `v0.5.330`: no matching commits returned.
- Searched repository branches for `v0.5.330`: no matching branches returned.
- Inspected `wordpress/hrn/human-relational-navigator.php` at:
  - `fix/hrn-missing-question-local-completion`
  - `fix/hrn-grounded-question-field-recovery`
- Both inspected branch versions declare plugin version `0.5.280`, not live `0.5.330`. Blob SHA for the inspected file: `5cf9b1ae1667980e592a8a139ed99ed0df7c4740`.

### Conclusion
The inspected GitHub branch copies are materially behind live v0.5.330 and are not authoritative replacements. The older v0.5.310 private backup is also not a safe replacement. Do not merge or deploy any of these sources to live merely to restore availability.

### Next permitted source route
Use a supported WordPress.com authenticated downloadable backup or hosting export to obtain the exact live plugin file. Inspect and hash it locally, then synchronize the byte-exact source into a recovery branch before making any change. Do not restore the WordPress site from backup.

## LAN source search

### Searches performed
- Searched repository files for `corpus-runtime.json` and `retrieval-index.json`: no indexed file matches returned.
- Searched repository branches for `corpus-runtime` and `retrieval-index`: no matching branches returned.
- PR #637 branch `recovery/lan-source-snapshot-20261015` contains the live-matching LAN engine and entrypoint snapshot plus QA/README/relationships export, but not the corpus or retrieval index.

### Conclusion
The recovery branch is not a deployable LAN reconstruction. The current relationships export explicitly says relationships are unavailable; do not infer a relationship graph from semantic co-occurrence or titles.

### Next permitted source route
Obtain an authenticated downloadable backup/export that includes the exact LAN plugin directory and relevant generated data/build inputs. Record the archive hash, internal file paths, sizes, and hashes of extracted artifacts. Compare against the live file inventory before treating any copy as authoritative.

## Scope and safety

- Searches covered the named repository's searchable commit and branch indexes and the listed file paths. They do not prove no artifact exists in another repository, a local computer, an unindexed branch, or a hosting backup.
- No production writes, WordPress restore, plugin mutation, or service changes were performed.
- Do not use broad or repeated requests to evade a blocked bulk export. Use the authenticated backup/export path or another supported, explicitly authorized transfer method.
