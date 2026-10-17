import { chromium } from "playwright";

const GUIDE_URL = "https://geralddaquila.com/the-guide/";
const QUERY = "Explain stewardship in everyday life without sending me to another page.";
const API_PATTERN = /\/api\/query(?:\?|$)/;

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
page.setDefaultTimeout(20_000);

try {
  const pageErrors = [];
  page.on("pageerror", error => pageErrors.push(error.message));

  await page.goto(GUIDE_URL, { waitUntil: "domcontentloaded", timeout: 60_000 });
  await page.locator("form#archive-search-form").first().waitFor({ state: "attached", timeout: 30_000 });

  const entryways = await page.evaluate(() => {
    const forms = Array.from(document.querySelectorAll("form#archive-search-form"));
    const woodySelector = '.archive-stage-wrapper[data-guide-instance="woody"]';
    return forms.map((form, index) => ({
      index,
      kind: form.closest(woodySelector) ? "woody" : "upper",
      hasInput: Boolean(form.querySelector("#archive-query-input")),
      hasButton: Boolean(form.querySelector("#archive-submit-btn")),
      root: form.closest(woodySelector) ? "woody" :
        (form.closest("#archive-container-top") ? "archive-container-top" : "ancestor-fallback")
    }));
  });

  const upperIndex = entryways.findIndex(item => item.kind === "upper");
  const woodyIndex = entryways.findIndex(item => item.kind === "woody");
  if (upperIndex < 0 || woodyIndex < 0) {
    throw new Error("Expected both upper CustomHTML and Woody entryways; discovered " + JSON.stringify(entryways));
  }
  for (const entry of entryways) {
    if (!entry.hasInput || !entry.hasButton) {
      throw new Error("Entryway is missing its query input or Search button: " + JSON.stringify(entry));
    }
  }

  async function exerciseEntryway(kind, index) {
    const form = page.locator("form#archive-search-form").nth(index);
    const input = form.locator("#archive-query-input");
    const button = form.locator("#archive-submit-btn");

    await input.fill(QUERY);
    const requests = [];
    const onRequest = request => {
      if (API_PATTERN.test(new URL(request.url()).pathname) && request.method() === "POST") {
        requests.push(request);
      }
    };
    page.on("request", onRequest);
    try {
      await Promise.all([
        page.waitForRequest(request =>
          API_PATTERN.test(new URL(request.url()).pathname) && request.method() === "POST",
          { timeout: 25_000 }
        ),
        button.click()
      ]);
      await page.waitForTimeout(1200);
    } finally {
      page.off("request", onRequest);
    }

    if (requests.length !== 1) {
      throw new Error(kind + " entryway generated " + requests.length +
        " observed POST /api/query requests for one click; expected exactly one.");
    }

    const rootSelector = kind === "woody"
      ? '.archive-stage-wrapper[data-guide-instance="woody"]'
      : "#archive-container-top";
    const root = page.locator(rootSelector).first();
    const responseBox = root.locator("#archive-response-box").first();
    const responseText = root.locator("#archive-response-text").first();

    await responseBox.waitFor({ state: "visible", timeout: 120_000 });
    await page.waitForFunction(({ selector, minLength }) => {
      const root = document.querySelector(selector);
      const text = root?.querySelector("#archive-response-text")?.innerText?.trim() || "";
      return text.length >= minLength && !/Giving this question a little more room/i.test(text);
    }, { selector: rootSelector, minLength: 80 }, { timeout: 120_000 });

    const answer = (await responseText.innerText()).trim();
    if (answer.length < 80) {
      throw new Error(kind + " entryway rendered an empty or too-short answer (" + answer.length + " chars).");
    }
    console.log(JSON.stringify({
      entryway: kind,
      requestCount: requests.length,
      requestUrl: requests[0].url(),
      answerChars: answer.length,
      answerVisible: await responseBox.isVisible()
    }));
  }

  await exerciseEntryway("upper", upperIndex);
  await exerciseEntryway("woody", woodyIndex);

  if (pageErrors.length) {
    throw new Error("Browser page errors: " + JSON.stringify(pageErrors));
  }
  console.log("PASS: both live entryways independently submitted exactly one request and rendered an answer.");
} finally {
  await browser.close();
}
