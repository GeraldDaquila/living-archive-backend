# Decision-rights calibration — Guide validation protocol

## Purpose

This is the visitor-facing validation path for the canonical decision-rights
initialization benchmark. The Guide page is the interface: submit each frozen
question through the normal question field. No private endpoint, synthetic
production request, or direct database mutation is required.

The canonical benchmark and review baseline are committed to `main`. The
companion runtime policy is implemented in the governed decision-rights
candidate-selection change; it must be merged and the primary Render service
must finish deploying that commit before the Guide page uses the new policy.
Do not infer runtime activation from the benchmark files alone.

Once active, explicit institutional decision-rights questions receive the three
CORE candidates. The delegated-judgment candidate is added only when delegation
is in scope; formal/informal institutional dynamics is added only when written
or formal rules and informal norms/practice are both present. Leadership versus
positional authority remains a separate related-only path. Ordinary chores and
underspecified questions do not activate this policy. Policy candidates carry a
governed role/condition, not a fabricated semantic-similarity score. If combined
conditions exceed the four-candidate envelope, the policy abstains rather than
silently truncating a required candidate.

## Submission order

Submit these questions individually through the Guide page, recording the
answer and visible behavior for each case:

1. **Central question:** How do decision rights affect institutional responsibility?
2. **Distributed authority:** Who should answer for an institutional decision when authority and influence are spread across several people?
3. **Delegated authority:** When a board delegates a consequential decision to a committee, who remains accountable and how can the decision be challenged?
4. **Formal/informal mismatch:** What happens when an institution's written decision rights differ from the informal norms that actually determine who gets heard and what gets decided?
5. **Leadership versus position:** How is leadership different from positional authority, and why does holding a title not necessarily mean someone leads?
6. **Negative control — garden:** How should I assign responsibilities when organizing a home garden?
7. **Negative control — household:** How should roommates divide routine household chores fairly?
8. **Underspecified control:** Who is responsible for this?

## What to inspect

For the first four cases, assess whether the answer actually addresses:
- formal decision mandate and its limits;
- actual influence over information, options, resources, and outcomes;
- proportional accountability based on influence, knowledge, role, and capacity;
- affected people's ability to question, challenge, and seek correction;
- delegation or informal practice only when the case calls for it.

For leadership-versus-position, assess that the answer makes that distinction without importing the whole institutional decision-rights framework. For the two ordinary chore cases, the Guide should answer the ordinary practical question without forcing institutional Gold Star disciplines into it. For the underspecified case, it should ask what situation or decision is meant rather than inventing context.

## Evidence boundary

A good visitor answer is necessary but does not, by itself, prove which candidate was retrieved or applied. Internal telemetry distinguishes candidate availability, provider-reported selection, response-span evidence, guidance exposure, and final delivery. A similarity score or provider assertion alone is not proof of substantive application.

This baseline is canonical for initialization, not independent ground truth or a production quality certificate. Record observed outcomes and request/trace identifiers where available. Do not silently alter the canonical labels, tune on the held-out cases, or infer that a successful answer validates every runtime stage.

## Release boundary

No production deployment or synthetic traffic is authorized by this protocol. Gerald's Workspace-primary remains the production reference; USE2-Mirror remains untouched until its scheduled reset. Any runtime change must be isolated, tested on GitHub Actions, and separately reviewed against the unchanged baseline before merge or deployment.
