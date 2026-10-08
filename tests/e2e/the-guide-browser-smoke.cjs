const assert = require("node:assert/strict");
const { chromium } = require("playwright");

const PAGE_URL = "https://geralddaquila.com/the-guide/";
const API_URL = "https://living-archive-backend.onrender.com/api/query";
const CANONICAL_URL = "https://geralddaquila.com/knowledge-memory-living-codices/";
const CANONICAL_TITLE = "Knowledge, Memory & Living Codices";

(async () => {
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    const queryRequests = [];
    const corsHeaders = {
      "access-control-allow-origin": "https://geralddaquila.com",
      "access-control-allow-methods": "POST, OPTIONS",
      "access-control-allow-headers": "content-type, authorization",
      "access-control-max-age": "600",
    };

    await page.route(API_URL, async (route) => {
      const request = route.request();
      if (request.method() === "OPTIONS") {
        await route.fulfill({ status: 204, headers: corsHeaders, body: "" });
        return;
      }

      queryRequests.push({
        method: request.method(),
        postData: request.postData(),
      });

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

    const paragraphs = await page.locator("#archive-response-text > p").count();
    assert.equal(paragraphs, 3, "all three answer paragraphs must remain visible");

    assert.equal(await recommendation.innerText(), CANONICAL_TITLE);
    assert.equal(await recommendation.getAttribute("href"), CANONICAL_URL);
    assert.equal(await recommendation.isVisible(), true);

    console.log("Guide browser E2E: PASS");
    console.log("visitor_submit_requests=1");
    console.log("answer_paragraphs=3");
    console.log("recommendation_visible=true");
    console.log("recommendation_url=canonical");
  } catch (error) {
    console.error("Guide browser E2E: FAIL");
    console.error(error && error.stack ? error.stack : error);
    process.exitCode = 1;
  } finally {
    if (browser) await browser.close();
  }
})();
