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
const apiFailures = [];
const apiFinished = [];
const pageErrors = [];
page.on("pageerror", error => pageErrors.push(error.message));
page.on("request", request => {
  if (request.method() === "POST" && request.url().includes("/api/query")) {
    let body = {};
    try { body = JSON.parse(request.postData() || "{}"); } catch {}
    apiRequests.push({ url: request.url(), body, atMs: elapsed() });
  }
});
page.on("response", response => {
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
  void response.json().then(payload => {
    record.payload = payload;
  }).catch(error => {
    record.bodyReadError = error?.message || String(error);
  });
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
  if (pageErrors.length) throw new Error("Browser page errors: " + pageErrors.join(" | "));

  console.log(JSON.stringify({
    stage: "live_e2e_passed",
    rendered,
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
