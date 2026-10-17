import { chromium } from "playwright";

const GUIDE_URL = "https://geralddaquila.com/the-guide/";
const QUERY = "Explain stewardship in everyday life without sending me to another page.";
const API_PATTERN = /\\/api\\/query(?:\\?|$)/;

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
page.setDefaultTimeout(15_000);
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
  if (/living-archive-guide|guide.*\\.js/i.test(response.url())) {
    scriptResponses.push({ url: response.url(), status: response.status() });
  }
});
page.on("requestfailed", request => {
  if (/living-archive-guide|guide.*\\.js/i.test(request.url())) {
    scriptFailures.push({ url: request.url(), error: request.failure()?.errorText || "unknown" });
  }
});
page.on("request", request => {
  if (request.method() === "POST" && API_PATTERN.test(new URL(request.url()).pathname)) {
    posts.push({ url: request.url(), postData: request.postData()?.slice(0, 500) || "" });
  }
});

async function diagnostics() {
  return page.evaluate(() => {
    const root = document.querySelector('.archive-stage-wrapper[data-guide-instance="woody"]');
    const form = root?.querySelector("form#archive-search-form");
    const button = form?.querySelector("#archive-submit-btn");
    const input = form?.querySelector("#archive-query-input");
    const rect = button?.getBoundingClientRect();
    const x = rect ? rect.left + rect.width / 2 : 0;
    const y = rect ? rect.top + rect.height / 2 : 0;
    const hit = button && rect ? document.elementFromPoint(x, y) : null;
    return {
      formFound: Boolean(form),
      inputLength: input?.value?.length ?? null,
      buttonDisabled: button?.disabled ?? null,
      buttonText: button?.innerText ?? null,
      buttonRect: rect ? { x: rect.x, y: rect.y, width: rect.width, height: rect.height } : null,
      centerHitTag: hit?.tagName ?? null,
      centerHitId: hit?.id ?? null,
      centerHitClass: typeof hit?.className === "string" ? hit.className : null,
      centerHitHTML: hit?.outerHTML?.slice(0, 600) ?? null,
      rootAttributes: root ? Object.fromEntries(Array.from(root.attributes).map(a => [a.name, a.value])) : null,
      scripts: Array.from(document.scripts).map(s => ({ src: s.src, type: s.type || "classic" }))
    };
  });
}

try {
  await page.goto(GUIDE_URL, { waitUntil: "domcontentloaded", timeout: 45_000 });
  const woody = page.locator('.archive-stage-wrapper[data-guide-instance="woody"]');
  await woody.waitFor({ state: "attached", timeout: 20_000 });
  const form = woody.locator("form#archive-search-form").first();
  const input = form.locator("#archive-query-input").first();
  const button = form.locator("#archive-submit-btn").first();
  await input.fill(QUERY);

  const requestWaiter = page.waitForRequest(request =>
    request.method() === "POST" && API_PATTERN.test(new URL(request.url()).pathname),
    { timeout: 20_000 }
  ).then(request => ({ request, error: null }), error => ({ request: null, error: error.message }));

  try {
    await button.click({ timeout: 10_000 });
  } catch (clickError) {
    throw new Error("Woody submit button could not be clicked. " + JSON.stringify({
      clickError: clickError.message,
      diagnostic: await diagnostics(),
      scriptResponses,
      scriptFailures,
      posts,
      pageErrors,
      consoleErrors
    }));
  }

  const requestResult = await requestWaiter;
  if (!requestResult.request) {
    throw new Error("Woody click produced no POST /api/query within 20 seconds. " +
      JSON.stringify({ diagnostic: await diagnostics(), scriptResponses, scriptFailures, posts, pageErrors, consoleErrors }));
  }

  if (posts.length !== 1) {
    throw new Error("Expected exactly one POST, observed " + posts.length + ". " + JSON.stringify(posts));
  }

  const responseBox = woody.locator("#archive-response-box").first();
  const responseText = woody.locator("#archive-response-text").first();
  await responseBox.waitFor({ state: "visible", timeout: 90_000 });
  await page.waitForFunction(() => {
    const root = document.querySelector('.archive-stage-wrapper[data-guide-instance="woody"]');
    const text = root?.querySelector("#archive-response-text")?.innerText?.trim() || "";
    return text.length >= 80 && !/Giving this question a little more room/i.test(text);
  }, null, { timeout: 90_000 });

  const answer = (await responseText.innerText()).trim();
  console.log(JSON.stringify({
    result: "WOODY_PASS",
    requestCount: posts.length,
    requestUrl: posts[0].url,
    answerChars: answer.length,
    answerVisible: await responseBox.isVisible(),
    scriptResponses,
    scriptFailures,
    pageErrors,
    consoleErrors
  }));
  if (pageErrors.length) throw new Error("Page errors after answer: " + JSON.stringify(pageErrors));
} catch (error) {
  console.error(error.stack || error.message);
  process.exitCode = 1;
} finally {
  await browser.close();
}
