# USE v391 Production Freeze

Protected visitor-experience baseline for The Guide.

## Canonical production commit

`9c6b4397c2e8541c6894cc4dcd153f0b852409e1`

## Protected application state

- `main.py` = v391
- Fingerprint = `USE-v391-grief-local-refinement-restored`
- Build ID = `USE-BUILD-v391-grief-local-refinement-restored`
- Protected `use_core.py` blob SHA = `fb3208a8d287f16562ffd640d89f65d5e8d18607`

## Freeze rule

Do not overwrite or replace the complete `main.py` engine when making later refinements.

Any future production change must begin from this exact commit and preserve the complete application structure. Changes should be surgical and limited to the intended visitor-experience defect.

`use_core.py` is protected and must remain byte-identical unless a separately declared architectural change explicitly reopens the protected core boundary.

## Known benchmark baseline

The grief benchmark question currently produces the approved v391 visitor experience, rated 9.2/10 during visual retest.

The benchmark should be used as a regression guard, not as a reason to reopen the retrieval/reasoning architecture unless a demonstrated visitor defect requires it.

## Freeze branch

`protected/v391-freeze` points to the canonical production commit above.
