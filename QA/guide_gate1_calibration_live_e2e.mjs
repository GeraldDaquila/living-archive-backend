import { chromium } from "playwright";

const GUIDE_URL = "https://geralddaquila.com/the-guide-find-your-way2/?qa_live=gate1-isolated";
const PRIMARY_API_ORIGIN = "https://living-archive-backend.onrender.com";
const MIRROR_API_ORIGIN = "https://living-archive-backend-mirror.onrender.com";
const EXPECTED_COMMIT = (process.env.EXPECTED_USE_COMMIT_SHA || "").trim();
const QUERY = "When a community faces a difficult trade-off between individual freedom and shared responsibility, how should it make a decision that is both fair and workable?";
const ROOT = ".archive-stage-wrapper[data-guide-instance='woody']";

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ serviceWorkers: "block" });
const page = await context.newPage();
page.setDefaultTimeout(60_000);
page.setDefaultNavigationTimeout(30_000);

const apiRequests = [];
const apiResponses = [];
const apiBodyReads = [];
const apiFailures = [];
const apiFinished = [];
const mirrorFallbacks = [];
const pageErrors = [];
const consoleErrors = [];
const startedAt = Date.now();
const elapsed = () => Date.now() - startedAt;

page.on("pageerror", error => pageErrors.push({
  name: error.name || "Error",
  message: error.message,
  stack: error.stack || ""
}));
page.on("console", message => {
  if (message.type() === "error") consoleErrors.push({
    text: message.text(),
    location: message.location()
  });
});

page.route(`${MIRROR_API_ORIGIN}/api/query*`, async route => {
  mirrorFallbacks.push({
    url: route.request().url(),
    atMs: elapsed(),
    reason: "secondary intentionally held offline until its December 1 reset"
  });
  await route.abort("blockedbyclient");
});

page.on("request", request => {
  if (request.method() !== "POST" || !request.url().includes("/api/query")) return;
  let body = {};
  try { body = JSON.parse(request.postData() || "{}"); } catch {}
  apiRequests.push({ url: request.url(), body, atMs: elapsed() });
});
page.on("response", response => {
  if (!response.url().includes("/api/query") || response.request().method() !== "POST") return;
  const record = {
    url: response.url(),
    status: response.status(),
    atMs: elapsed(),
    payload: null,
    bodyReadError: null
  };
  apiResponses.push(record);
  apiBodyReads.push(
    response.json()
      .then(payload => { record.payload = payload; })
      .catch(error => { record.bodyReadError = error?.message || String(error); })
  );
});
page.on("requestfailed", request => {
  if (request.method() === "POST" && request.url().includes("/api/query")) {
    apiFailures.push({
      url: request.url(),
      atMs: elapsed(),
      error: request.failure()?.errorText || "unknown"
    });
  }
});
page.on("requestfinished", request => {
  if (request.method() === "POST" && request.url().includes("/api/query")) {
    apiFinished.push({ url: request.url(), atMs: elapsed() });
  }
});

try {
  // Verify the production instance is the expected deployed main commit before
  // submitting the one-question calibration. This avoids testing a rolling build.
  const readinessDeadline = Date.now() + 180_000;
  let readiness = null;
  let readinessError = null;
  while (Date.now() < readinessDeadline) {
    try {
      const response = await page.request.get(
        `${PRIMARY_API_ORIGIN}/api/provider-health-readiness`,
        { timeout: 10_000 }
      );
      readiness = await response.json();
      if (
        response.ok() &&
        readiness?.ok === true &&
        (!EXPECTED_COMMIT || readiness.deployment_commit_sha === EXPECTED_COMMIT)
      ) break;
      readinessError = {
        status: response.status(),
        version: readiness?.version,
        commit: readiness?.deployment_commit_sha
      };
    } catch (error) {
      readinessError = error?.message || String(error);
    }
    await new Promise(resolve => setTimeout(resolve, 5_000));
  }
  if (
    !readiness ||
    readiness.ok !== true ||
    (EXPECTED_COMMIT && readiness.deployment_commit_sha !== EXPECTED_COMMIT)
  ) {
    throw new Error("Primary production readiness did not match the expected deployment: " +
      JSON.stringify({ expectedCommit: EXPECTED_COMMIT, readiness, readinessError }));
  }

  console.log(JSON.stringify({
    stage: "gate1_live_calibration_start",
    expectedCommit: EXPECTED_COMMIT || null,
    deployedCommit: readiness.deployment_commit_sha,
    version: readiness.version,
    query: QUERY
  }));

  await page.goto(GUIDE_URL, { waitUntil: "domcontentloaded" });
  await page.waitForLoadState("load").catch(() => {});
  const root = page.locator(ROOT);
  await root.waitFor({ state: "attached" });
  const input = root.locator("#archive-query-input");
  const submit = root.locator("#archive-submit-btn");
  const answer = root.locator("#archive-response-text");
  await input.waitFor({ state: "visible" });
  await submit.waitFor({ state: "visible" });

  await input.fill(QUERY);
  await submit.evaluate(element => setTimeout(() => element.click(), 0));

  const responseDeadline = Date.now() + 55_000;
  while (
    !apiResponses.some(item => item.payload?.query === QUERY) &&
    Date.now() < responseDeadline
  ) {
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  await Promise.all(apiBodyReads);

  const primaryResponse = apiResponses.find(item =>
    item.url.startsWith(PRIMARY_API_ORIGIN) &&
    item.status === 200 &&
    item.payload?.query === QUERY
  );
  if (!primaryResponse) {
    throw new Error("The isolated Gate 1 question did not receive a complete HTTP 200 response from primary: " +
      JSON.stringify({
        apiRequests,
        apiResponses: apiResponses.map(item => ({
          url: item.url,
          status: item.status,
          payloadQuery: item.payload?.query,
          intent: item.payload?.intent,
          response: typeof item.payload?.response === "string" ? item.payload.response.slice(0, 1800) : null,
          answerBasis: item.payload?.answer_basis || null,
          bodyReadError: item.bodyReadError
        })),
        apiFailures,
        apiFinished,
        mirrorFallbacks,
        pageErrors,
        consoleErrors
      })
    );
  }

  const payload = primaryResponse.payload;
  const responseText = String(payload.response || "").replace(/\\s+/g, " ").trim();
  if (
    payload.intent !== "TOPICAL_INQUIRY" ||
    responseText.length < 150 ||
    !/freedom/i.test(responseText) ||
    !/responsibility/i.test(responseText) ||
    !/fair/i.test(responseText)
  ) {
    throw new Error("Primary returned an answer that did not satisfy the calibration relevance contract: " +
      JSON.stringify({
        status: primaryResponse.status,
        intent: payload.intent,
        answerBasis: payload.answer_basis || null,
        response: responseText.slice(0, 2400),
        recommendation: payload.recommendation || null
      })
    );
  }

  await page.waitForFunction(selector => {
    const node = document.querySelector(selector + " #archive-response-text");
    const text = (node?.innerText || "").toLowerCase();
    return text.length >= 100 &&
      text.includes("freedom") &&
      text.includes("responsibility") &&
      text.includes("fair");
  }, ROOT, { timeout: 45_000 });

  const visibleAnswer = (await answer.innerText()).replace(/\\s+/g, " ").trim();
  if (
    !visibleAnswer.toLowerCase().includes("freedom") ||
    !visibleAnswer.toLowerCase().includes("responsibility") ||
    !visibleAnswer.toLowerCase().includes("fair")
  ) {
    throw new Error("The API response was not retained in the visible Guide answer: " + visibleAnswer);
  }

  console.log(JSON.stringify({
    stage: "gate1_live_calibration_response_rendered",
    query: QUERY,
    answerBasis: payload.answer_basis || null,
    recommendation: payload.recommendation || null,
    requestId: payload.request_id || payload.requestId || null,
    apiResponse: responseText.slice(0, 2400),
    visibleAnswer: visibleAnswer.slice(0, 2400),
    primaryPostCount: apiRequests.filter(item => item.url.startsWith(PRIMARY_API_ORIGIN)).length,
    mirrorFallbacks,
    pageErrors,
    consoleErrors
  }));
} catch (error) {
  console.error(JSON.stringify({
    stage: "gate1_live_calibration_failed",
    error: error?.stack || String(error),
    apiRequests,
    apiResponses: apiResponses.map(item => ({
      url: item.url,
      status: item.status,
      payloadQuery: item.payload?.query,
      intent: item.payload?.intent,
      response: typeof item.payload?.response === "string" ? item.payload.response.slice(0, 1800) : null,
      answerBasis: item.payload?.answer_basis || null,
      bodyReadError: item.bodyReadError
    })),
    apiFailures,
    apiFinished,
    mirrorFallbacks,
    pageErrors,
    consoleErrors
  }));
  process.exitCode = 1;
} finally {
  await browser.close();
}
