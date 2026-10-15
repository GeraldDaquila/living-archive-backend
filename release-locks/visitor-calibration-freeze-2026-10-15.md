# Living Archive Ecosystem Freeze — Visitor Calibration Baseline

**Freeze established:** 2026-10-15  
**Purpose:** Hold the integrated ecosystem constant while Gerald performs actual visitor calibration of individual specialist tools.  
**Change policy:** NO CODE, PROMPT, ROUTING, COMPOSITION, PROVIDER, FRONTEND, WORDPRESS, OR DEPLOYMENT CHANGES DURING CALIBRATION unless a reproducible blocker prevents the visitor test from proceeding. Any exception must be documented as a separate defect, approved explicitly, and applied only after preserving this baseline.

## Baseline identity

### General-purpose USE — primary and mirror
- Repository: `GeraldDaquila/living-archive-backend`
- Frozen production commit: `130508d48495f959b6fe9aca4411cee9ed40504d`
- Release: `v489.260`
- Fingerprint: `USE-v489.260-workplace-relational-return`
- Canonical source SHA-256 returned by both services: `85eecc82a2e5f1d08139ecc083ab36f32fc0c0816260da48b955c9553f1ea4ae`
- Primary URL: https://living-archive-backend.onrender.com
- Mirror URL: https://living-archive-backend-mirror.onrender.com
- Verified on 2026-10-15: both deployments live on the same commit; stewardship general-purpose query returned a substantive answer and a separate canonical recommendation on both.

### HRN — WordPress specialist boundary
- Protected writer: `plugins/human-relational-navigator/human-relational-navigator.php`, version `0.5.330`; do not edit during calibration.
- Composition guard: `plugins/living-archive-hrn-composition-contract-guard/living-archive-hrn-composition-contract-guard.php`, version `1.3.6`; live WordPress change ID `5194`, file size 12,253 bytes.
- Provider deadline guard: `la-provider-bridge-deadline` v1.2.0.
- HRN latency guard: v1.2.0.
- Provider bank bridge: v0.2.1.
- Streaming transport: v0.1.0.
- Command boundary adapter: v1.3.0.
- Frozen USE core: `use_core.py`; untouched.
- Live checks on 2026-10-15: recurring-argument opening, manager-trust opening, parent-care, friend-distance, dismissed/withdraw cycle, and repair-without-total-blame responses returned HTTP 200 with contextual questions. Repair-without-blame mismatch was corrected in guard v1.3.6.

### Mini-USE / Catalogue
- Repository: `GeraldDaquila/mini-use-payhip`
- Production service: https://mini-use-payhip.onrender.com
- Render service ID: `srv-dami28f40ujc73b15ej0`
- Branch: `main`
- Auto-deploy: disabled
- Last live deployment verified: `M0.15.70`, commit `d2fd087cf7923fc02ddc108ed36fa01d6de5c42e`, deployed 2026-10-14.
- No deployment or source changes are authorized during visitor calibration.

## Frozen interaction contract
1. The visitor begins in the public-facing tool and sees a useful, human response.
2. The specialist remains in its own voice and does not become a diagnosis, prescription, or generic machine Q&A.
3. The journey progresses through exploration, useful distinction, synthesis, and movement without repeating the same question genre.
4. The visitor can complete the journey through the established CTA/browser interaction.
5. On closure, the specialist returns a bounded, relevant canonical recommendation to USE; USE remains responsible for the final recommendation and visitor-facing handover.
6. The general-purpose USE gold-standard response composition and routing remain constant.
7. Primary and mirror remain aligned; mini-USE remains at its pinned production deployment.
8. Existing safety behavior and access boundaries remain unchanged.

## Calibration rules
- Treat browser CTA/handover as accepted from the prior established baseline, as directed by the project steward; do not reopen that resolved issue unless the visitor reproduces it.
- Record each visitor test as observation/evidence against this fixed baseline.
- Do not fix a specialist issue in the middle of a calibration run. Capture the exact prompt, turn, output, expected behavior, and impact; finish or stop the run, then open a separate defect.
- A defect may not be addressed by changing the general-purpose USE baseline unless the failure is demonstrated to originate there.
- No dependency/provider/model swaps, broad refactors, prompt rewrites, cache-policy changes, or deployment changes during calibration.
- If a live baseline identity changes unexpectedly, stop calibration and restore/verify the baseline before proceeding.
- Only explicit steward authorization ends this freeze. After calibration, changes proceed as isolated specialist defects with regression checks against this frozen baseline.

## Verification status at freeze
- Primary USE and mirror: live and aligned at v489.260 / commit above.
- USE general-purpose regression: passed on both services.
- HRN live API calibration samples: passed for tested opening/context cases after guard v1.3.6.
- Browser-level interaction: accepted as previously solved for purposes of this calibration, per steward direction.
- End-to-end ecosystem freeze: operational change-control lock; Render primary and mirror auto-deploy remain configured as enabled. Avoid all pushes to their `main` branch during this freeze. No source/deployment change should be made absent an explicit exception.

This document is the reference point for visitor calibration. Do not amend it to fit test results; record test results separately.
