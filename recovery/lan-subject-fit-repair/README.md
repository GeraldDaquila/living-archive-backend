# LAN subject-fit repair — review artifact

**Status: draft / not deployable.** This branch preserves the PR #637 recovery snapshot and adds a separate proposed engine file plus an isolated regression fixture. It does not modify WordPress production.

## Source provenance recovered

An existing Library package, `public-living-archive-navigator-v0.3.3-DUPLICATE-TITLE-GUARD-COLOR-NEUTRAL.zip`, contains the complete v0.3.3 package, including both runtime data files. Its `includes/class-lan-engine.php` Git blob SHA-1 is `bf54ad254cfa906c000bd9ce27b641be5c07a692`, exactly matching the blob SHA of the recovered live engine snapshot. This verifies the package engine is byte-identical to the recovered snapshot.

The package contains:
- `data/corpus-runtime.json`: 2,581,911 bytes, SHA-256 `5a9cd89b5f2962f39015449a375e5a45a5bfd9dd3bb66899b017b66449b78446`
- `data/retrieval-index.json`: 4,213,390 bytes, SHA-256 `b6c417e626b075098f2740bc90a337b2c1781073a67ba1849c5f82dd57507033`
- 1,603 public resources (T1 809, T2 775, T3 19), 13,433 indexed terms
- relationships remain explicitly unavailable; no relationship edges are inferred.

This corrects the earlier recovery snapshot's limitation: those artifacts were missing from PR #637, but an existing complete package has now been located and verified against the recovered engine source. The package is an older v0.3.3 artifact; its runtime data has not yet been proven identical to the exact live filesystem copy by hashes from WordPress, so retain that provenance distinction.

## Proposed structural repair

The proposed engine:
1. derives subject-focus terms from the visitor's words, excluding navigation boilerplate;
2. lets explicit subject terms participate in retrieval even when their document frequency exceeds the broad-term cutoff;
3. ranks the candidate window by direct title/excerpt/category/body evidence for the stated subject;
4. applies a hard subject-fit threshold before planning;
5. revalidates model-selected destinations and returns a clarification/insufficient-evidence response rather than padding with unrelated resources when fewer than three relevant destinations remain;
6. keeps deterministic fallback within the already validated candidate set.

No changes are made to the General Purpose Guide, HRN, use_core.py, the live WordPress site, or Render deployments.

## QA evidence

Verified locally against the recovered v0.3.3 runtime/index:
- PHP syntax check: pass
- isolated subject-fit regression fixture: pass
- existing LAN engine regression suite: pass
- real-corpus institutional-responsibility candidate selection: pass; selected three grounded resources:
  - Institutional Stewardship
  - Institutional Cornerstones
  - Why Institutional Collapse Often Begins as Psychological Disconnection

The visual-shell test was not a valid pass in this local environment because its pinned SPE 3.4.0 CSS reference file was absent; the test failed at that external fixture comparison before exercising the subject-fit code. No visual files were changed.

These are local package/fixture results, not live WordPress E2E. The live endpoint must be re-tested after code review and an authorized release process.