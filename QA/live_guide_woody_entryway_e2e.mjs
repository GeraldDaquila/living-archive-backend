import { chromium } from "playwright";

const GUIDE_URL = "https://geralddaquila.com/the-guide-find-your-way2/";
const QUERY = "What does stewardship mean in everyday life, and why does it matter now more than ever?";
const API_PATTERN = /\/api\/query(?:\?|$)/;
const mark = (stage, details = {}) => console.log(JSON.stringify({ stage, at: new Date().toISOString(), ...details }));

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
page.setDefaultTimeout(8_000);
page.setDefaultNavigationTimeout(25_000);
const pageErrors = [];
const consoleErrors = [];
const scriptResponses = [];
const scriptFailures = [];
const posts = [];

page.on("pageerror", error => pageErrors.push(error.message));
page.on("console", message => {
  if (message.type() === "error") consoleErrors.push(message.text());
});
page.on("response", response => {
  if (/living-archive-guide|guide.*\.js/i.test(response.url())) {
    scriptResponses.push({ url: response.url(), status: response.status() });
  }
});
page.on("requestfailed", request => {
  if (/living-archive-guide|guide.*\.js/i.test(request.url())) {
    scriptFailures.push({ url: request.url(), error: request.failure()?.errorText || "unknown" });
  }
});
page.on("request", request => {
  if (request.method() === "POST" && API_PATTERN.test(new URL(request.url()).pathname)) {
    posts.push({ url: request.url(), postData: request.postData()?.slice(0, 500) || "" });
    mark("api_post_observed", { url: request.url() });
  }
});

async function diagnostics() {
  return page.evaluate(() => {
    const root = document.querySelector('.archive-stage-wrapper[data-guide-instance="woody"]');
    const form = root?.querySelector("form#archive-search-form");
    const button = form?.querySelector("#archive-submit-btn");
    const input = form?.querySelector("#archive-query-input");
    const rect = button?.getBoundingClientRect();
    const hit = button && rect ? document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2) : null;
    return {
      formFound: Boolean(form),
      inputLength: input?.value?.length ?? null,
      buttonDisabled: button?.disabled ?? null,
      buttonText: button?.innerText ?? null,
      buttonRect: rect ? { x: rect.x, y: rect.y, width: rect.width, height: rect.height } : null,
      centerHitTag: hit?.tagName ?? null,
      centerHitId: hit?.id ?? null,
      centerHitClass: typeof hit?.className === "string" ? hit.className : null,
      centerHitHTML: hit?.outerHTML?.slice(0, 400) ?? null,
      rootAttributes: root ? Object.fromEntries(Array.from(root.attributes).map(a => [a.name, a.value])) : null,
      scripts: Array.from(document.scripts).map(s => ({ src: s.src, type: s.type || "classic" }))
    };
  }, null, { timeout: 5_000 });
}

try {
  mark("navigation_start", { url: GUIDE_URL });
  await page.goto(GUIDE_URL, { waitUntil: "domcontentloaded", timeout: 25_000 });
  mark("navigation_complete", { title: await page.title() });
  const woody = page.locator('.archive-stage-wrapper[data-guide-instance="woody"]');
  await woody.waitFor({ state: "attached", timeout: 8_000 });
  mark("woody_wrapper_found");
  const form = woody.locator("form#archive-search-form").first();
  const input = form.locator("#archive-query-input").first();
  const button = form.locator("#archive-submit-btn").first();
  await input.fill(QUERY);
  mark("query_filled", { query: QUERY });

  const requestWaiter = page.waitForRequest(request =>
    request.method() === "POST" && API_PATTERN.test(new URL(request.url()).pathname),
    { timeout: 12_000 }
  ).then(request => ({ request, error: null }), error => ({ request: null, error: error.message }));

  const preClick = await diagnostics();
  mark("pre_click_diagnostic", preClick);
  const clickOutcome = await Promise.race([
    button.click({ timeout: 4_000 }).then(() => ({ kind: "playwright_click_completed" }), error => ({ kind: "playwright_click_error", message: error.message })),
    new Promise(resolve => setTimeout(() => resolve({ kind: "playwright_click_watchdog" }), 4_500))
  ]);
  mark("playwright_click_outcome", clickOutcome);
  if (clickOutcome.kind !== "playwright_click_completed") {
    const domClick = await page.evaluate(() => {
      const root = document.querySelector('.archive-stage-wrapper[data-guide-instance="woody"]');
      const button = root?.querySelector("form#archive-search-form #archive-submit-btn");
      const rect = button?.getBoundingClientRect();
      const hit = rect ? document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2) : null;
      const result = { buttonFound: Boolean(button), hitTag: hit?.tagName ?? null, hitId: hit?.id ?? null, hitClass: typeof hit?.className === "string" ? hit.className : null };
      button?.click();
      return result;
    });
    mark("dom_click_fallback", domClick);
  }

  const requestResult = await requestWaiter;
  if (!requestResult.request) {
    throw new Error("Woody click produced no POST /api/query within 12 seconds. " +
      JSON.stringify({ diagnostic: await diagnostics(), scriptResponses, scriptFailures, posts, pageErrors, consoleErrors }));
  }
  if (posts.length !== 1) {
    throw new Error("Expected exactly one POST, observed " + posts.length + ". " + JSON.stringify(posts));
  }

  const responseBox = woody.locator("#archive-response-box").first();
  const responseText = woody.locator("#archive-response-text").first();
  await responseBox.waitFor({ state: "visible", timeout: 8_000 });
  await page.waitForFunction(() => {
    const root = document.querySelector('.archive-stage-wrapper[data-guide-instance="woody"]');
    const text = root?.querySelector("#archive-response-text")?.innerText?.trim() || "";
    return text.length >= 80 && !/Giving this question a little more room/i.test(text);
  }, null, { timeout: 60_000 });
  const answer = (await responseText.innerText()).trim();
  console.log(JSON.stringify({
    result: "WOODY_PASS",
    requestCount: posts.length,
    requestUrl: posts[0].url,
    answerChars: answer.length,
    answerVisible: await responseBox.isVisible(),
    answerPreview: answer.slice(0, 350),
    scriptResponses, scriptFailures, pageErrors, consoleErrors
  }));
  if (pageErrors.length) throw new Error("Page errors after answer: " + JSON.stringify(pageErrors));
} catch (error) {
  mark("woody_test_failed", { message: error.message, stack: error.stack, scriptResponses, scriptFailures, posts, pageErrors, consoleErrors });
  process.exitCode = 1;
} finally {
  await browser.close();
}
