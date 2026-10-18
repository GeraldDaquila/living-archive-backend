import { chromium } from "playwright";

const GUIDE_URL = "https://geralddaquila.com/the-guide-find-your-way2/";
const API_PATTERN = /\/api\/query(?:\?|$)/;
const ROOT = ".archive-stage-wrapper[data-guide-instance='woody']";
const QUESTIONS = [
  "What does stewardship mean in everyday life?",
  "How might this shape the way people make decisions together?",
  "What is one concrete way to practice this in a neighborhood?"
];
const ASSISTANT_ANSWERS = [
  "Stewardship means caring responsibly for something entrusted to you, such as shared spaces, time, or relationships. Small acts of care help preserve what others rely on.",
  "People make better decisions together when they can speak honestly while still considering the needs of the group. Shared responsibility works best when disagreement is safe and practical.",
  "A neighborhood can practice stewardship by maintaining a shared garden or common space together. That makes care visible, distributes responsibility, and gives neighbors a reason to cooperate. What shared place in your neighborhood could benefit from that kind of care?"
];
const FOLLOWUP = "Can you explain your previous answer in simpler terms?";
const mark = (stage, details = {}) => console.log(JSON.stringify({ stage, ...details }));

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
const page = await context.newPage();
page.setDefaultTimeout(8_000);
page.setDefaultNavigationTimeout(25_000);

const pageErrors = [];
const consoleErrors = [];
const failedRequests = [];
const apiRequests = [];
page.on("console", message => { if (message.type() === "error") consoleErrors.push(message.text()); });
page.on("requestfailed", request => failedRequests.push({ url: request.url(), error: request.failure()?.errorText || "unknown" }));
let mainQueryIndex = 0;
page.on("pageerror", error => pageErrors.push(error.message));

await page.route("**/api/query**", async route => {
  const request = route.request();
  if (request.method() !== "POST" || !API_PATTERN.test(new URL(request.url()).pathname)) {
    await route.continue();
    return;
  }

  let body = {};
  try { body = JSON.parse(request.postData() || "{}"); } catch {}
  apiRequests.push({ body, postData: request.postData() || "", url: request.url() });
  const query = String(body.query || "");
  let answer;
  if (query === FOLLOWUP) {
    answer = "In simpler terms, stewardship means looking after what you and others depend on, without assuming you must control everything.";
  } else {
    const expectedIndex = QUESTIONS.indexOf(query);
    if (expectedIndex < 0) {
      await route.fulfill({ status: 400, contentType: "application/json", body: JSON.stringify({ ok: false, error: "Unexpected QA query" }) });
      return;
    }
    mainQueryIndex = Math.max(mainQueryIndex, expectedIndex + 1);
    answer = ASSISTANT_ANSWERS[expectedIndex];
  }

  await route.fulfill({
    status: 200,
    contentType: "application/json",
    headers: { "access-control-allow-origin": "*" },
    body: JSON.stringify({
      ok: true,
      version: "qa-ui-contract",
      fingerprint: "qa-ui-contract-mock-only",
      source_sha256: "qa-only",
      request_id: "qa-" + apiRequests.length,
      query,
      intent: "TOPICAL_INQUIRY",
      response: answer,
      recommendation: null,
      answer_basis: { kind: "general_knowledge", label: "General knowledge", explanation: "QA fixture response only." },
      processing: "qa_mock",
      route_source: "qa_ui_contract",
      visitor_boundary_version: "qa"
    })
  });
});

try {
  mark("test_start", { url: GUIDE_URL, mode: "intercepted_mock_api_only" });
  await page.goto(GUIDE_URL, { waitUntil: "domcontentloaded" });
  const root = page.locator(ROOT);
  await root.waitFor({ state: "attached" });
  const input = root.locator("#archive-query-input");
  const submit = root.locator("#archive-submit-btn");
  const answer = root.locator("#archive-response-text");
  await input.waitFor({ state: "visible" });
  await submit.waitFor({ state: "visible" });
  await page.waitForTimeout(1500);
  mark("controller_ready_diagnostics", {
    rootCount: await root.count(),
    inputCount: await input.count(),
    inputVisible: await input.isVisible().catch(() => false),
    submitCount: await submit.count(),
    submitVisible: await submit.isVisible().catch(() => false),
    submitDisabled: await submit.isDisabled().catch(() => null),
    answerCount: await answer.count(),
    controllerScripts: await page.locator("script[src*='living-archive-guide']").evaluateAll(nodes => nodes.map(n => n.src)),
    pageUrl: page.url(),
    consoleErrors,
    failedRequests
  });

  await page.evaluate(() => {
    window.__guideSubmitTrace = [];
    document.addEventListener("click", event => {
      if (event.target?.closest?.("#archive-submit-btn")) {
        window.__guideSubmitTrace.push({ event: "submit_button_click_capture", defaultPrevented: event.defaultPrevented });
      }
    }, true);
    document.addEventListener("submit", event => {
      if (event.target?.querySelector?.("#archive-submit-btn")) {
        window.__guideSubmitTrace.push({ event: "form_submit_capture", defaultPrevented: event.defaultPrevented, action: event.target.action, method: event.target.method });
        // Prevent only native document navigation so the test can observe whether
        // the live controller's submit handler issues the API request. Do not stop
        // propagation: the controller's normal handler must still run.
        event.preventDefault();
      }
    }, true);
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
      window.__guideSubmitTrace.push({ event: "fetch_called", url: String(args[0]?.url || args[0]) });
      return originalFetch.apply(this, args);
    };
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url, ...rest) {
      window.__guideSubmitTrace.push({ event: "xhr_open", method, url: String(url) });
      return originalOpen.call(this, method, url, ...rest);
    };
  });
  mark("submit_trace_installed", { note: "Capture click, form-submit, fetch and XHR before first interaction." });

  for (let i = 0; i < QUESTIONS.length; i++) {
    const before = await answer.innerText().catch(() => "");
    await input.fill(QUESTIONS[i]);
    const responsePromise = page.waitForResponse(response =>
      response.request().method() === "POST" && API_PATTERN.test(new URL(response.url()).pathname),
      { timeout: 12_000 }
    ).then(response => ({ response }), error => ({ error }));
    let clickError = null;
    try {
      // Dispatch the real DOM click without Playwright waiting on a possible native
      // form navigation; the capture-phase submit guard above keeps the document
      // available while the controller handler and API request are observed.
      await submit.evaluate(element => element.click());
    } catch (error) {
      clickError = error.message;
    }
    mark("post_click_diagnostics", {
      index: i + 1,
      query: QUESTIONS[i],
      pageUrl: page.url(),
      clickError,
      submitTrace: await page.evaluate(() => window.__guideSubmitTrace || []).catch(error => [{ evaluationError: error.message }]),
      apiRequests,
      failedRequests,
      pageErrors,
      consoleErrors
    });
    const responseResult = await responsePromise;
    if (responseResult.error) {
      mark("api_response_timeout_diagnostics", {
        index: i + 1,
        query: QUESTIONS[i],
        clickError,
        submitTrace: await page.evaluate(() => window.__guideSubmitTrace || []).catch(error => [{ evaluationError: error.message }]),
        apiRequests,
        consoleErrors,
        failedRequests,
        pageErrors,
        message: responseResult.error.message
      });
      throw new Error("No matching API response after submit interaction: " + responseResult.error.message);
    }
    const response = responseResult.response;
    if (response.status() !== 200) throw new Error("Mock API response was not HTTP 200 for main query " + (i + 1));
    await page.waitForFunction(({ selector, before }) => {
      const current = document.querySelector(selector)?.innerText?.trim() || "";
      return current.length > 35 && current !== before.trim();
    }, { selector: ROOT + " #archive-response-text", before });
    mark("main_query_rendered", { index: i + 1, query: QUESTIONS[i], answerLength: (await answer.innerText()).length });
  }

  const panelInput = root.locator("#archive-ordinary-followup-input");
  await panelInput.waitFor({ state: "visible", timeout: 8_000 });
  const replyButton = root.getByRole("button", { name: /reply/i }).first();
  const answerBeforeReply = await answer.innerText();
  await panelInput.fill(FOLLOWUP);
  const replyResponsePromise = page.waitForResponse(response =>
    response.request().method() === "POST" && API_PATTERN.test(new URL(response.url()).pathname)
  );
  await replyButton.click();
  const replyResponse = await replyResponsePromise;
  if (replyResponse.status() !== 200) throw new Error("Mock API reply did not return HTTP 200");

  await page.waitForFunction(({ selector, before }) => {
    const current = document.querySelector(selector)?.innerText?.trim() || "";
    return current.length > 35 && current !== before.trim();
  }, { selector: ROOT + " #archive-response-text", before: answerBeforeReply });

  const replyRequest = apiRequests[apiRequests.length - 1];
  const serialized = JSON.stringify(replyRequest?.body || {});
  // Main-form Search is intentionally a fresh inquiry and resets older turns.
  // The dedicated Reply should carry the immediately preceding question and answer,
  // not unrelated questions submitted as separate main-form searches.
  const expectedHistoryItems = [QUESTIONS[2], ASSISTANT_ANSWERS[2]];
  const foundHistoryItems = expectedHistoryItems.filter(item => serialized.includes(item));
  const historyFieldPresent = Object.keys(replyRequest?.body || {}).some(key => /history|conversation|messages|turns/i.test(key));
  const continuityPassed = historyFieldPresent && foundHistoryItems.length === expectedHistoryItems.length;

  mark("ordinary_reply_contract", {
    panelAppearedNaturallyFromMockResponse: true,
    replyRequestObserved: true,
    replyRequestStatus: replyResponse.status(),
    replyRequestBodyKeys: Object.keys(replyRequest?.body || {}),
    historyFieldPresent,
    expectedHistoryItemCount: expectedHistoryItems.length,
    foundHistoryItemCount: foundHistoryItems.length,
    foundHistoryItems,
    continuityPassed,
    pageErrors,
    note: "API responses were intercepted and mocked; this verifies the live WordPress controller UI contract only, not backend behavior."
  });

  if (apiRequests.length !== 4) throw new Error("Expected exactly 4 intercepted API requests, got " + apiRequests.length);
  if (!continuityPassed) throw new Error("Ordinary Reply request did not carry the expected prior conversation history.");
  if (pageErrors.length) throw new Error("Browser page errors: " + pageErrors.join(" | "));
  mark("test_passed", { requestCount: apiRequests.length, continuityPassed, consoleErrors, failedRequests });
} catch (error) {
  mark("test_failed", { message: error.message, requestCount: apiRequests.length, pageErrors });
  process.exitCode = 1;
} finally {
  await browser.close();
}
