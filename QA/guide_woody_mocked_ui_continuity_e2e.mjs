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
const apiRequests = [];
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

  for (let i = 0; i < QUESTIONS.length; i++) {
    const before = await answer.innerText().catch(() => "");
    await input.fill(QUESTIONS[i]);
    const responsePromise = page.waitForResponse(response =>
      response.request().method() === "POST" && API_PATTERN.test(new URL(response.url()).pathname)
    );
    await submit.click();
    const response = await responsePromise;
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
  const expectedHistoryItems = [...QUESTIONS, ASSISTANT_ANSWERS[2]];
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
  mark("test_passed", { requestCount: apiRequests.length, continuityPassed });
} catch (error) {
  mark("test_failed", { message: error.message, requestCount: apiRequests.length, pageErrors });
  process.exitCode = 1;
} finally {
  await browser.close();
}
