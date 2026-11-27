import assert from "node:assert/strict";
import vm from "node:vm";
import { readFileSync } from "node:fs";

const controller = readFileSync("wordpress/living-archive-answer-doorway-standard/assets/guide-controller-v489.333.js","utf8");
const start = controller.indexOf("function hasInternalGuideLanguage");
const end = controller.indexOf("/* ================================================================\n   SAFETY BOUNDARY", start);
const safetyStart = controller.indexOf("function hasAuthoritativeSafetyPayload");
const safetyEnd = controller.indexOf("function naturalizeSafetyMessage", safetyStart);
assert.ok(start >= 0 && end > start && safetyStart > end && safetyEnd > safetyStart);
const functions = controller.slice(start,end) + "\n" + controller.slice(safetyStart,safetyEnd);

async function scenario(queue) {
  const calls = [];
  const context = {
    USE_PRIMARY_ENDPOINT: "https://primary.test/api/query",
    USE_SECONDARY_ENDPOINT: "https://secondary.test/api/query",
    USE_TRANSPORT_TIMEOUT_MS: 1000,
    console: { warn(){}, info(){}, error(){} },
    setTimeout, clearTimeout,
    fetch: async endpoint => {
      calls.push(endpoint);
      const next = queue.shift();
      if (next instanceof Error) throw next;
      return next;
    }
  };
  vm.runInNewContext(functions + "\nthis.runFetchUSE = fetchUSE;", context);
  return { calls, run: context.runFetchUSE };
}
const response = (status, payload) => ({
  ok: status >= 200 && status < 300, status,
  clone: () => ({ json: async () => payload })
});

{
  const s = await scenario([response(503,{ok:false,failure_kind:"application_contract",retryable:false,error_type:"gold_star_v2_quality_floor_rejected"})]);
  await assert.rejects(() => s.run({query:"x"},"query"), e => e.name === "GuideApplicationContractError" && e.failureKind === "application_contract" && e.retryable === false);
  assert.equal(s.calls.length,1,"application rejection must not fail over");
}
{
  const s = await scenario([new Error("network down"),response(200,{ok:true,response:"A useful visitor answer."})]);
  const result = await s.run({query:"x"},"query");
  assert.equal(result.status,200);
  assert.equal(s.calls.length,2,"transport failure must try secondary");
  assert.match(s.calls[1],/secondary/);
}
{
  const s = await scenario([new Error("primary down"),new Error("secondary down")]);
  await assert.rejects(() => s.run({query:"x"},"query"), e => e.name === "GuideTransportError" && e.failureKind === "transport" && e.retryable === true);
  assert.equal(s.calls.length,2,"both transport endpoints should be attempted");
}
{
  const s = await scenario([response(200,null)]);
  await assert.rejects(() => s.run({query:"x"},"query"), e => e.name === "GuideApplicationContractError" && e.reason === "invalid_json_envelope");
  assert.equal(s.calls.length,1,"malformed HTTP 200 must not fail over");
}
console.log("PASS: v489.333 application rejection / transport failover behavior");
