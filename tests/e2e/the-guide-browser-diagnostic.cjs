const assert = require("node:assert/strict");
const { chromium } = require("playwright");

const PAGE_URL = "https://geralddaquila.com/the-guide/";
const CANONICAL_URL = "https://geralddaquila.com/knowledge-memory-living-codices/";
const CANONICAL_TITLE = "Knowledge, Memory & Living Codices";

(async () => {
  let browser;
  let page;
  const queryRequests = [];
  const browserErrors = [];
  const failedRequests = [];
  const apiResponses = [];

  try {
    browser = await chromium.launch({ headless: true });
    page = await browser.newPage();

    page.on("console", (message) => {
      if (message.type() === "error") browserErrors.push(message.text());
    });
    page.on("pageerror", (error) => browserErrors.push(error.message));
    page.on("requestfailed", (request) => {
      failedRequests.push({
        url: request.url(),
        method: request.method(),
        error: request.failure() ? request.failure().errorText : "unknown",
      });
    });
    page.on("response", (response) => {
      if (response.url().includes("/api/query")) {
        apiResponses.push({ url: response.url(), status: response.status() });
      }
    });

    await page.route("**/api/query*", async (route) => {
      const request = route.request();
      const requestedHeaders =
        request.headers()["access-control-request-headers"] ||
        "content-type, authorization";
      const corsHeaders = {
        "access-control-allow-origin": "*",
        "access-control-allow-methods": "POST, OPTIONS",
        "access-control-allow-headers": requestedHeaders,
        "access-control-max-age": "600",
      };

      if (request.method() === "OPTIONS") {
        await route.fulfill({ status: 204, headers: corsHeaders, body: "" });
        return;
      }

      queryRequests.push({
        url: request.url(),
        method: request.method(),
        postData: request.postData(),
      });
      console.log("intercepted_query_request=" + request.method() + " " + request.url());

      await route.fulfill({
        status: 200,
        headers: corsHeaders,
        contentType: "application/json; charset=utf-8",
        body: JSON.stringify({
          intent: "TOPICAL_INQUIRY",
          processing: "basic_inquiry",
          request_id: "guide-browser-e2e",
          response: [
            "Stewardship means taking responsibility for something that matters beyond yourself.",
            "Our choices can affect people and systems beyond our immediate reach.",
            "A useful next step is to ask what is ours to care for, and how to care for it well.",
          ].join("\n\n"),
          recommendation: {
            title: "📖 Knowledge, Memory & Living Codices",
            url: CANONICAL_URL,
          },
        }),
      });
    });

    await page.goto(PAGE_URL, { waitUntil: "domcontentloaded", timeout: 60000 });
    const input = page.locator("#archive-query-input");
    await input.waitFor({ state: "visible", timeout: 30000 });
    await input.fill("What is stewardship, and why does it matter today?");
    await page.locator("#archive-submit-btn").click();

    const recommendation = page.locator(
      "#archive-response-text .archive-inline-recommendation a"
    );
    await recommendation.waitFor({ state: "visible", timeout: 30000 });

    assert.equal(queryRequests.length, 1, "one visitor submit must produce exactly one API request");
    assert.equal(queryRequests[0].method, "POST", "Guide must use POST for /api/query");
    assert.equal(await page.locator("#archive-response-text > p").count(), 3);
    assert.equal(await recommendation.innerText(), CANONICAL_TITLE);
    assert.equal(await recommendation.getAttribute("href"), CANONICAL_URL);

    console.log("Guide browser E2E: PASS");
    console.log("visitor_submit_requests=1");
    console.log("answer_paragraphs=3");
    console.log("recommendation_visible=true");
    console.log("recommendation_url=canonical");
  } catch (error) {
    let responseText = "<missing>";
    let legacyRecommendation = "<missing>";
    if (page) {
      responseText = await page.locator("#archive-response-text").innerText().catch(() => "<missing>");
      legacyRecommendation = await page.locator("#archive-recommendation").innerText().catch(() => "<missing>");
    }
    console.error("Guide browser E2E: FAIL");
    console.error(error && error.stack ? error.stack : error);
    console.error("queryRequests=" + JSON.stringify(queryRequests));
    console.error("apiResponses=" + JSON.stringify(apiResponses));
    console.error("browserErrors=" + JSON.stringify(browserErrors));
    console.error("failedRequests=" + JSON.stringify(failedRequests));
    console.error("responseText=" + JSON.stringify(responseText));
    console.error("legacyRecommendation=" + JSON.stringify(legacyRecommendation));
    process.exitCode = 1;
  } finally {
    if (browser) await browser.close();
  }
})();
