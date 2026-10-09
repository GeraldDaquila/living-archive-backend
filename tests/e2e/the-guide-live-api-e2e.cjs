const assert = require("node:assert/strict");
const { chromium } = require("playwright");

const PAGE_URL = "https://geralddaquila.com/the-guide/";
const API_HOST = "https://living-archive-backend.onrender.com/api/query";

(async () => {
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    const apiRequests = [];
    const pageErrors = [];

    page.on("request", (request) => {
      if (request.url().includes("/api/query") && request.method() === "POST") {
        apiRequests.push({ url: request.url(), method: request.method() });
      }
    });
    page.on("pageerror", (error) => pageErrors.push(error.message));

    await page.goto(PAGE_URL, { waitUntil: "domcontentloaded", timeout: 60000 });
    const form = page.locator("#archive-search-form");
    await form.waitFor({ state: "visible", timeout: 30000 });

    await page.locator("#archive-query-input").fill(
      "What is stewardship and why is it important now more than ever?"
    );

    const apiResponsePromise = page.waitForResponse(
      (response) =>
        response.url().includes("/api/query") &&
        response.request().method() === "POST",
      { timeout: 90000 }
    );

    await page.locator("#archive-submit-btn").click();
    const apiResponse = await apiResponsePromise;
    assert.equal(apiResponse.status(), 200, "live Guide API must return HTTP 200");

    const payload = await apiResponse.json();
    assert.ok(
      typeof payload.response === "string" && payload.response.trim().length > 0,
      "live API must return answer text"
    );
    assert.ok(
      payload.recommendation &&
      typeof payload.recommendation.title === "string" &&
      typeof payload.recommendation.url === "string",
      "live API must return structured recommendation metadata"
    );
    assert.match(
      payload.recommendation.url,
      /^https:\/\/geralddaquila\.com\/\S+$/,
      "live recommendation must use a canonical Living Archive URL"
    );

    const visibleLink = page.locator(
      "#archive-response-text .archive-inline-recommendation a, #archive-recommendation a"
    ).filter({ visible: true }).first();

    await visibleLink.waitFor({ state: "visible", timeout: 30000 });
    assert.equal(await visibleLink.getAttribute("href"), payload.recommendation.url);
    assert.ok((await visibleLink.innerText()).trim().length > 0);
    assert.equal(apiRequests.length, 1, "one submission must make exactly one live API request");
    assert.deepEqual(pageErrors, [], "Guide page must not emit uncaught JavaScript errors");

    console.log("Guide live API E2E: PASS");
    console.log("live_api_status=" + apiResponse.status());
    console.log("visitor_submit_requests=" + apiRequests.length);
    console.log("answer_text_visible=true");
    console.log("recommendation_visible=true");
    console.log("recommendation_url_matches_api=true");
  } catch (error) {
    console.error("Guide live API E2E: FAIL");
    console.error(error && error.stack ? error.stack : error);
    process.exitCode = 1;
  } finally {
    if (browser) await browser.close();
  }
})();
