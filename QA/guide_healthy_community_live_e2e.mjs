import { chromium } from "playwright";

const GUIDE_URL = "https://geralddaquila.com/the-guide-find-your-way2/?qa_live=healthy-community-20261022";
const QUERY = "I'm new to the Living Archive. I care about healthier communities, but I don't know its vocabulary or where to begin.";
const EXPECTED_TITLE = "What Healthy Communities Actually Look Like";
const EXPECTED_URL = "https://geralddaquila.com/2025/10/07/t4-codex-overflow-communities-governance-by-resonance/";
const ROOT = ".archive-stage-wrapper[data-guide-instance='woody']";

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ serviceWorkers: "block" });
const page = await context.newPage();
page.setDefaultTimeout(60_000);
page.setDefaultNavigationTimeout(30_000);

const startedAt = Date.now();
const elapsed = () => Date.now() - startedAt;
const apiRequests = [];
const apiResponses = [];
const apiBodyReads = [];
const apiFailures = [];
const apiFinished = [];
const controllerRequests = [];
const controllerResponses = [];
const controllerBodyReads = [];
const pageErrors = [];
page.on("pageerror", error => pageErrors.push(error.message));
page.on("request", request => {
  if (request.url().includes("living-archive-guide-") && request.url().endsWith(".js?ver=5")) {
    controllerRequests.push({ url: request.url(), atMs: elapsed() });
  }
  if (request.method() === "POST" && request.url().includes("/api/query")) {
    let body = {};
    try { body = JSON.parse(request.postData() || "{}"); } catch {}
    apiRequests.push({ url: request.url(), body, atMs: elapsed() });
  }
});
page.on("response", response => {
  if (response.url().includes("living-archive-guide-") && response.url().includes(".js")) {
    const record = { url: response.url(), status: response.status(), atMs: elapsed(), timeoutMs: null, bodyReadError: null };
    controllerResponses.push(record);
    controllerBodyReads.push(response.text().then(source => {
      const match = source.match(/USE_TRANSPORT_TIMEOUT_MS\s*=\s*(\d+)/);
      record.timeoutMs = match ? Number(match[1]) : "constant_not_found";
      record.sourceBytes = source.length;
    }).catch(error => { record.bodyReadError = error?.message || String(error); }));
  }
  if (!response.url().includes("/api/query")) return;
  // Record headers/status synchronously; body parsing must never hide the fact
  // that a response arrived from the failure diagnostics.
  const record = {
    url: response.url(),
    status: response.status(),
    atMs: elapsed(),
    payload: null,
    bodyReadError: null
  };
  apiResponses.push(record);
  apiBodyReads.push(response.json().then(payload => {
    record.payload = payload;
  }).catch(error => {
    record.bodyReadError = error?.message || String(error);
  }));
});
page.on("requestfailed", request => {
  if (request.url().includes("/api/query")) {
    apiFailures.push({ url: request.url(), atMs: elapsed(), error: request.failure()?.errorText || "unknown" });
  }
});
page.on("requestfinished", request => {
  if (request.url().includes("/api/query")) {
    apiFinished.push({ url: request.url(), atMs: elapsed() });
  }
});

try {
  console.log(JSON.stringify({ stage: "live_e2e_start", url: GUIDE_URL }));
  await page.goto(GUIDE_URL, { waitUntil: "domcontentloaded" });
  // Wait for the external controller response and inspect the exact bytes the browser received.
  await page.waitForLoadState("load").catch(() => {});
  await Promise.all(controllerBodyReads);
  console.log(JSON.stringify({ stage: "controller_script_diagnostic", controllerRequests, controllerResponses }));
  const root = page.locator(ROOT);
  await root.waitFor({ state: "attached" });
  const input = root.locator("#archive-query-input");
  const submit = root.locator("#archive-submit-btn");
  const answer = root.locator("#archive-response-text");
  await input.waitFor({ state: "visible" });
  await submit.waitFor({ state: "visible" });
  await input.fill(QUERY);

  // Use a DOM click so the test observes the actual live controller without
  // Playwright auto-waiting on a possible form navigation.
  await submit.evaluate(element => setTimeout(() => element.click(), 0));

  const link = root.locator("#archive-response-text a.archive-recommendation-link");
  await link.waitFor({ state: "visible", timeout: 60_000 });
  const rendered = await link.evaluate(node => ({
    title: node.innerText.trim(),
    href: node.href,
    visible: Boolean(node.getClientRects().length)
  }));
  const responseText = await answer.innerText();
  // The link proves the UI rendered; now wait for the separately captured API
  // bodies before validating the response contract.
  await Promise.all(apiBodyReads);
  if (rendered.title !== EXPECTED_TITLE) {
    throw new Error("Live visitor link title mismatch: " + JSON.stringify(rendered));
  }
  if (rendered.href !== EXPECTED_URL) {
    throw new Error("Live visitor link URL mismatch: " + JSON.stringify(rendered));
  }
  if (!responseText.includes("A healthy community")) {
    throw new Error("The substantive answer was not rendered before the recommendation.");
  }
  if (!apiRequests.some(request => request.body.query === QUERY)) {
    throw new Error("No real production /api/query request carried the acceptance query.");
  }
  if (!apiResponses.some(item =>
    item.status === 200 &&
    item.payload?.recommendation?.title === EXPECTED_TITLE &&
    item.payload?.recommendation?.url === EXPECTED_URL
  )) {
    throw new Error("The real production API did not return the exact canonical recommendation pair.");
  }
  // Exercise the exact conceptual question that previously fell through to the
  // evidence-limitation message despite four canonical bodies passing the recovery gates.
  // The live acceptance contract now requires a substantive Archive-backed answer and
  // a destination drawn from the same vetted canonical evidence set.
  const conceptualQuery = "What is the role of trust in community stewardship?";
  await input.fill(conceptualQuery);
  await submit.evaluate(element => setTimeout(() => element.click(), 0));
  await page.waitForFunction(() => {
    const el = document.querySelector("#archive-response-text");
    return !!el && /trust|stewardship/i.test(el.innerText || "");
  }, null, { timeout: 60_000 });
  const conceptualText = await answer.innerText();
  await Promise.all(apiBodyReads);
  const conceptualResponses = apiResponses.filter(item =>
    item.payload && item.payload.query === conceptualQuery
  );
  if (!apiRequests.some(request => request.body.query === conceptualQuery)) {
    throw new Error("No real production /api/query request carried the conceptual trust/stewardship query.");
  }
  const supportedResponse = conceptualResponses.find(item =>
    item.status === 200 &&
    item.payload?.intent === "TOPICAL_INQUIRY" &&
    item.payload?.answer_basis?.kind !== "archive_evidence_unavailable" &&
    typeof item.payload?.response === "string" &&
    item.payload.response.trim().length >= 120 &&
    item.payload?.recommendation &&
    /^https:\/\/geralddaquila\.com\//i.test(item.payload.recommendation.url || "")
  );
  if (!supportedResponse) {
    throw new Error("Conceptual trust/stewardship question did not return an Archive-grounded answer and canonical recommendation. Responses: " +
      JSON.stringify(conceptualResponses.map(item => ({
        status:item.status,
        intent:item.payload?.intent,
        answer_basis:item.payload?.answer_basis,
        recommendation:item.payload?.recommendation,
        response:item.payload?.response
      }))));
  }
  if (!conceptualText.includes(supportedResponse.payload.response.slice(0, 60))) {
    // The UI may render punctuation/formatting differences, so require a substantial
    // overlap rather than exact whole-string equality.
    const normalizedUI = conceptualText.replace(/\s+/g, " ").trim().toLowerCase();
    const normalizedAPI = supportedResponse.payload.response.replace(/\s+/g, " ").trim().toLowerCase();
    const overlap = normalizedAPI.split(/[.!?]+/).map(part=>part.trim()).filter(part=>part.length>20)
      .filter(part=>normalizedUI.includes(part.slice(0, Math.min(part.length, 48))));
    if (overlap.length === 0) {
      throw new Error("The browser did not render a meaningful portion of the Archive-grounded API answer.");
    }
  }
  if (await root.locator("#archive-response-text a.archive-recommendation-link").count() !== 1) {
    throw new Error("The conceptual response must render exactly one canonical recommendation link.");
  }
  const conceptualLink = await root.locator("#archive-response-text a.archive-recommendation-link").first().evaluate(el=>({
    href:el.href,
    text:(el.innerText||el.textContent||"").trim()
  }));
  if (conceptualLink.href !== supportedResponse.payload.recommendation.url) {
    throw new Error("The conceptual recommendation URL does not match the API-selected canonical destination.");
  }
  if (conceptualText.toLowerCase().includes("glossary")) {
    throw new Error("The conceptual question was visibly redirected to the Glossary.");
  }
  if (pageErrors.length) throw new Error("Browser page errors: " + pageErrors.join(" | "));

  console.log(JSON.stringify({
    stage: "live_e2e_passed",
    conceptualQuery,
    conceptualText,
    rendered,
    rendered,
    elapsedMs: elapsed(),
    controllerRequests,
    controllerResponses,
    apiRequests,
    apiResponses: apiResponses.map(item => ({
      url: item.url,
      status: item.status,
      atMs: item.atMs,
      recommendation: item.payload?.recommendation,
      bodyReadError: item.bodyReadError
    })),
    apiFailures,
    apiFinished,
    answerLength: responseText.length,
    pageErrors
  }));
} catch (error) {
  console.error(JSON.stringify({
    stage: "live_e2e_failed",
    message: error.message,
    elapsedMs: elapsed(),
    apiRequests,
    apiResponses: apiResponses.map(item => ({
      url: item.url,
      status: item.status,
      atMs: item.atMs,
      recommendation: item.payload?.recommendation,
      bodyReadError: item.bodyReadError
    })),
    apiFailures,
    apiFinished,
    pageErrors
  }));
  process.exitCode = 1;
} finally {
  await browser.close();
}
