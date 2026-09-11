# USE v334 Generation Contract

## Purpose

This is the release gate for reducing the fixed provider-generation envelope without weakening retrieval or visitor-facing constitutional behavior.

## Baseline failure

The current validated v334 runtime has recorded provider preflight failures with a fixed system/user envelope of approximately 4.6K characters before retrieved evidence is added. The compact path is also approximately 4.6K. This means the provider can be rejected before evidence selection can materially help it fit.

## Change boundary

The proposed intervention may reduce duplicated or overlapping fixed generation instructions only. It must not reduce or rewrite:

- canonical evidence selection or source authority;
- protected primary-resource and recommendation authority;
- exact resource title/URL provenance;
- evidence-grounded synthesis and navigation behavior;
- sovereignty and non-advisory boundaries;
- the v334 vulnerable-experience / compassionate recommendation boundary;
- final-answer safety validation.

## Required envelope behavior

The lean envelope must still tell the provider, in compact form, to:

1. answer the visitor's actual question rather than expose internal reasoning;
2. use supplied evidence as the authority for resource claims;
3. identify the adjudicated canonical resource when recommendation intent is present;
4. explain fit from the supplied evidence rather than invent visitor outcomes;
5. preserve uncertainty and avoid turning Archive material into personal advice;
6. preserve exact canonical links where provided;
7. return only a finished visitor-facing answer in the required output structure.

## v334 vulnerable-experience invariant

For grief, bereavement, loss, or comparable vulnerable-experience requests, the provider must not assert that an Archive resource offers or provides comfort, healing, peace, closure, meaning, purpose, or hope to the visitor or to people who are grieving. Such themes may be described as themes or claims represented by the source itself.

## Measurement gate

Before promotion, measure the fixed envelope with empty retrieved evidence using the same generation-message builder and the same provider preflight estimator used by production. Record normal and compact fixed-input character counts.

Acceptance requires that at least one real provider candidate passes preflight with the lean envelope under the configured provider input and total-size limits. A deterministic fallback caused solely by fixed-envelope size is not an acceptable release state.

## Regression probes

Run at minimum:

- the known grief recommendation query;
- a normal topical inquiry;
- a recommendation query requiring an exact canonical title and link;
- an open-exploration query that should remain navigational rather than advisory.

For the grief probe, inspect the final answer specifically for prohibited asserted visitor-benefit language. For recommendation probes, verify that the canonical resource identity and URL remain intact.

## Promotion rule

No change to production `main` is authorized from this branch until the envelope measurement and regression gates above are satisfied and the complete changed unit has been audited end-to-end.