# Post-deployment Guide verification — 2026-10-25

**Type:** manual production verification through Cowboy MCP.  
**Important:** This report is manually scored against the registry and held-out rubric; it is not a downloaded artifact from the GitHub Actions live-evaluation workflow. The evaluator correction in PR #879 was identified during this review and is being tested separately.

## Runtime identity

| Field | Primary | Mirror |
|---|---|---|
| Service | https://living-archive-backend.onrender.com | https://living-archive-backend-mirror.onrender.com |
| Render deploy | dep-dbenpkijnfac73e0p7r0 | dep-dbenpkijnfac73e0p790 |
| Deployed commit | e26f42f16000d7a10672cd8494b0d62489ee3fac | e26f42f16000d7a10672cd8494b0d62489ee3fac |
| Reported runtime version | v489.297 | v489.297 |
| Fingerprint | USE-v489.297-human-voice-conceptual-fallback | USE-v489.297-human-voice-conceptual-fallback |
| Reported source SHA-256 | efa8203712b6827ca5c6671d38a48630b6a1b0e89464ae7e961bef3d6be5042c | efa8203712b6827ca5c6671d38a48630b6a1b0e89464ae7e961bef3d6be5042c |

The version/fingerprint strings remained the existing v489.297 identity, but both services reported the same new runtime source hash after deploying commit e26f42f. Both services returned HTTP 200 for every probe.

## Summary

| Target | Registered gold-standard questions | Held-out questions | Result |
|---|---:|---:|---|
| Primary | 8/8 response/reference checks passed | 3/3 bounded checks passed | PASS, with human review still required |
| Mirror | 8/8 response/reference checks passed | 3/3 bounded checks passed | PASS, with human review still required |

The eight registered responses matched their stored reference text in both services. Registered no-doorway behavior and specified doorway titles/URLs were also observed. The held-out responses now satisfy the intended checks without being promoted to gold standards.

## Held-out results

| Case | Primary request ID | Mirror request ID | Result |
|---|---|---|---|
| Water boiling-point paraphrase | basic-c00d0864b8b3df6c | basic-c00d0864b8b3df6c | PASS: directly states 100°C (212°F), explains altitude/pressure, no unrelated doorway. |
| Cosmology and lived significance | basic-efff36a6acc5d2be | basic-efff36a6acc5d2be | PASS: defines cosmology, explains separation-based and unity-informed views without judging the visitor, gives a concrete conditional example, no unsolicited doorway. |
| Practical trust | basic-6f60240675d4d32e | basic-6f60240675d4d32e | PASS: concrete actions precede a focused follow-up; no unsolicited doorway or internal jargon. |

## Registered reference probes

| Benchmark | Request ID | Observed |
|---|---|---|
| Stewardship | basic-ec47bc29297f891f | Exact reference; no doorway, honoring the explicit request. |
| Reciprocity | basic-0b155fc0cad05590 | Exact reference; registered doorway title. The registry does not specify a URL for this title, so no URL equality is asserted. |
| Practical trust application | basic-731a795be23a898d | Accepted reference; no unsolicited doorway. |
| Accountability, trust, and harm repair | basic-c3d891024b8dec8c | Accepted reference; no unsolicited doorway. |
| Human development | basic-7b65a5fcababbb16 | Exact three-paragraph reference and registered doorway. |
| Water boiling point | basic-8deaea5cd795717c | Exact concise two-paragraph general-knowledge reference; no doorway. |
| Living Archive cosmology | basic-25796ab676910caf | Exact three-paragraph reference and registered doorway. |
| First principles | basic-36f447825e84c2a8 | Exact three-paragraph reference, all six principles, registered doorway. |

## Provenance and human review

- General boiling-point knowledge is labelled as general knowledge and explicitly not attributed to the Archive.
- The cosmology held-out response is labelled as an Archive reference and states that it is a starting explanation, not an exhaustive account of the Archive's cosmology.
- The practical-trust held-out response is labelled general knowledge because no sufficiently relevant Archive resource was identified. This is transparent rather than a false claim of canonical attribution; human review should still decide whether that provenance label is the best fit.
- The human-review scorecard is now part of the merged evaluation framework. These automated/manual smoke checks do not replace scoring of humane voice, Archive grounding, sentence coherence, paragraph construction, proportionality, and visitor orientation.
- No lessons were promoted automatically. No WordPress content was written. `use_core.py` was not changed.

## Next operational step

Merge PR #879 only after its checks pass, then run the manual GitHub Actions **Guide Live Evaluation** workflow to capture a formal JSON report with all responses, runtime identity, registry/suite hashes, and pending human scorecards. Review any difference between the formal evaluator and this manual scoring before treating the pipeline as production-ready.
