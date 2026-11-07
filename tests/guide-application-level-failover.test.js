const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");

const sourcePath = path.join(__dirname, "..", "frontend", "the-guide-frontend-v489.251.js");
const source = fs.readFileSync(sourcePath, "utf8");
const start = source.indexOf("async function useGuideApplicationFailureReason(response)");
const end = source.indexOf("/* ================================================================\n   SAFETY BOUNDARY", start);
assert.notEqual(start, -1, "retry classification helper must exist");
assert.notEqual(end, -1, "transport function boundary must exist");
const transportSource = source.slice(start, end);

function response(status, body) {
  return {
    ok: status >= 200 && status < 300,
    status,
    clone() {
      return { json: async () => body };
    }
  };
}

function harness(queue, options = {}) {
  const calls = [];
  const context = {
    USE_PRIMARY_ENDPOINT: "primary",
    USE_SECONDARY_ENDPOINT: "secondary",
    USE_PREDICTIVE_SHADOW_ENDPOINT: "shadow",
    useGuidePredictiveShadowRequested: () => Boolean(options.shadow),
    useTransportRetryableStatus: status => [500, 502, 503, 504, 522, 524].includes(status),
    fetchUSEEndpoint: async endpoint => {
      calls.push(endpoint);
      const next = queue.shift();
      if (next instanceof Error) throw next;
      return next;
    },
    console: { info() {}, warn() {}, error() {} },
    Error
  };
  vm.runInNewContext(transportSource, context);
  return { fetchUSE: context.fetchUSE, calls };
}

test("HTTP 200 application_generation_failure retries the secondary", async () => {
  const first = response(200, {
    ok: false,
    error_type: "application_generation_failure",
    response: "Please try again."
  });
  const second = response(200, { ok: true, response: "Substantive answer." });
  const h = harness([first, second]);

  const result = await h.fetchUSE({ query: "test" }, "qa");

  assert.deepEqual(h.calls, ["primary", "secondary"]);
  assert.equal(result, second);
});

test("HTTP 200 answer_integrity_failure retries the secondary", async () => {
  const first = response(200, {
    ok: true,
    response: "I could not produce a reliable answer.",
    answer_basis: { kind: "answer_integrity_failure" }
  });
  const second = response(200, { ok: true, response: "Recovered answer." });
  const h = harness([first, second]);

  const result = await h.fetchUSE({ query: "test" }, "qa");

  assert.deepEqual(h.calls, ["primary", "secondary"]);
  assert.equal(result, second);
});

test("ordinary successful answers are not retried", async () => {
  const first = response(200, { ok: true, response: "A valid answer." });
  const h = harness([first, response(200, { ok: true, response: "unused" })]);

  const result = await h.fetchUSE({ query: "test" }, "qa");

  assert.deepEqual(h.calls, ["primary"]);
  assert.equal(result, first);
});

test("safety responses and specialist handoffs are not retried", async () => {
  const safety = response(200, {
    ok: true,
    intent: "SAFETY_INTERRUPT",
    safety_message: "Safety response."
  });
  const handoff = response(200, {
    ok: true,
    intent: "GLOSSARY_HANDOFF",
    glossary_url: "https://example.invalid/glossary"
  });

  const safetyHarness = harness([safety]);
  assert.equal(await safetyHarness.fetchUSE({ query: "test" }, "qa"), safety);
  assert.deepEqual(safetyHarness.calls, ["primary"]);

  const handoffHarness = harness([handoff]);
  assert.equal(await handoffHarness.fetchUSE({ query: "test" }, "qa"), handoff);
  assert.deepEqual(handoffHarness.calls, ["primary"]);
});

test("existing retryable HTTP failures still use the secondary", async () => {
  const failed = response(503, { ok: false, error_type: "unavailable" });
  const recovered = response(200, { ok: true, response: "Recovered." });
  const h = harness([failed, recovered]);

  assert.equal(await h.fetchUSE({ query: "test" }, "qa"), recovered);
  assert.deepEqual(h.calls, ["primary", "secondary"]);
});

test("predictive-shadow acceptance mode never falls through to production", async () => {
  const failed = response(200, {
    ok: false,
    error_type: "application_generation_failure"
  });
  const h = harness([failed], { shadow: true });

  await assert.rejects(h.fetchUSE({ query: "test" }, "qa"));
  assert.deepEqual(h.calls, ["shadow"]);
});
