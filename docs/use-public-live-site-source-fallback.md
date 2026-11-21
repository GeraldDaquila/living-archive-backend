# USE live-site canonical evidence recovery

## Source hierarchy

1. The internal canonical corpus and Constitutional Register remain primary.
2. The versioned public crosslink snapshot supplies the bounded candidate set.
3. Candidate WordPress IDs and exact canonical URLs are intersected before source-body retrieval.
4. Source bodies are fetched through the read-only **Living Archive Canonical Evidence Bridge** endpoint:
   `/wp-json/living-archive/v1/canonical-evidence/{id}`.
5. The bridge checks published status, password protection, and viewable post type; reads stored content without running `the_content`, theme rendering, or shortcodes; normalizes markup; and returns a bounded text body with source modified time and canonical URL.

## Fallback trigger

The existing retrieval path remains primary. The public snapshot / WordPress search expansion runs only when:
- internal canonical retrieval is empty;
- an existing internal evidence gate explicitly reports unavailable/insufficient evidence (frame-neutral, question-structure, substantive sufficiency, or question-fit); or
- the visitor explicitly asks for a recommendation/navigation destination under the existing policy.

When internal evidence passes its gates, the fallback is not consulted. Recovered sources re-enter the existing canonical doorway and evidence-selection flow; they do not bypass it.

## Access and provenance

Only snapshot assets already classified as public/open and identified as published WordPress posts/pages are eligible. The bridge independently rejects non-published, password-protected, or non-viewable resources. The runtime verifies the returned WordPress ID, exact canonical URL, and source marker against the snapshot before accepting text.

Each accepted document carries source endpoint, canonical URL, title, WordPress ID, source modified timestamp, retrieval timestamp, and truncation state. Failures are closed and leave the existing abstention/recovery path intact. No query text or source passage is written to logs.

This is answer-grounding evidence only. It is not paired LLM/deterministic capture, held-out evaluation, observed visitor application, or outcome evidence, and cannot substantiate an adaptive-quality claim.
