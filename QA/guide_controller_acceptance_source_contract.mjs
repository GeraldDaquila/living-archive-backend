import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const path = "wordpress/living-archive-answer-doorway-standard/assets/guide-controller-v489.332.js";
const source = readFileSync(path, "utf8");

assert.match(source, /USE_FRONTEND_BUILD\s*=\s*'v489\.332-typed-visitor-acceptance'/);
assert.match(source, /response\.clone\(\)\.json\(\)/, "must inspect a clone and preserve the caller's response body");
assert.match(source, /error\.failureKind\s*=\s*'application_contract'/);
assert.match(source, /error\.retryable\s*=\s*false/);
assert.match(source, /data\.visitor_acceptance_contract/);
assert.match(source, /function validateGuideApplicationPayload\(/);
assert.match(source, /function hasAuthoritativeSafetyPayload\(/);
assert.match(source, /RELATIONAL_HANDOFF/);
assert.match(source, /GuideApplicationContractError/);
assert.match(source, /GuideTransportError/);
assert.match(source, /The Guide could not provide an answer that met its response standards/);
assert.match(source, /The Guide is temporarily unavailable/);
assert.doesNotMatch(source, /guidePayloadHasRejectedAnswerState/, "old duplicated semantic validator must stay removed");

const start = source.indexOf("async function fetchUSE(payload, requestLabel)");
const end = source.indexOf("\n/* ================================================================", start + 1);
assert.ok(start >= 0 && end > start, "fetchUSE must remain a bounded, inspectable function");
const fetchUse = source.slice(start, end);
const transportCatch = fetchUse.indexOf("} catch (transportError) {");
const applicationReject = fetchUse.indexOf("applicationPayload.failure_kind === 'application_contract'");
const retryStatus = fetchUse.indexOf("useTransportRetryableStatus(response.status)");
assert.ok(transportCatch > 0 && applicationReject > transportCatch,
  "application rejection must be handled outside the transport-only catch");
assert.ok(retryStatus > applicationReject,
  "application rejection must be classified before retryable HTTP status handling");
assert.match(fetchUse, /throw createGuideApplicationContractError\(/,
  "typed application rejection must terminate the request rather than fall through to failover");

console.log("PASS: v489.332 visitor acceptance source contract");
