import { chromium } from "playwright";

const GUIDE_URL = "https://geralddaquila.com/the-guide/";
const QUERY = "Explain stewardship in everyday life without sending me to another page.";
const API_PATTERN = /\/api\/query(?:\?|$)/;

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
page.setDefaultTimeout(20_000);

try {
  const pageErrors = [];
  const consoleErrors = [];
  page.on("pageerror", error => pageErrors.push(error.message));
  page.on("console", message => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });

  // Observe actual listener registration and script responses; do not assume
  // undocumented dataset markers exist in either controller.
  await page.addInitScript(() => {
    window.__guideE2EListenerTrace = [];
    const originalAdd = EventTarget.prototype.addEventListener;
    EventTarget.prototype.addEventListener = function(type, listener, options) {
      try {
        const target = this;
        if (["click", "submit", "input", "change"].includes(type)) {
          const isGlobal = target === window || target === document;
          const element = target instanceof Element ? target : null;
          const form = element?.matches?.("form#archive-search-form")
            ? element : element?.closest?.("form#archive-search-form");
          const isRelevantAncestor = element && (
            element.matches?.("#archive-container-top, .archive-stage-wrapper, body, html") ||
            element.closest?.("#archive-container-top, .archive-stage-wrapper")
          );
          if (isGlobal || form || isRelevantAncestor) {
            window.__guideE2EListenerTrace.push({
              type,
              target: target === window ? "window" : target === document ? "document" :
                (element?.tagName || "unknown") + (element?.id ? "#" + element.id : ""),
              formIndex: form ? Array.from(document.querySelectorAll("form#archive-search-form")).indexOf(form) : null
            });
          }
        }
      } catch (_) {}
      return originalAdd.call(this, type, listener, options);
    };
  });

  const scriptResponses = [];
  const browserEvents = [];
  page.on("requestfailed", request => {
    if (/living-archive-guide|guide.*\.js|\.js(?:\?|$)/i.test(request.url())) {
      browserEvents.push({ kind: "script-request-failed", url: request.url(), error: request.failure()?.errorText || "unknown" });
    }
  });
  page.on("response", response => {
    if (/living-archive-guide|guide.*\.js|\.js(?:\?|$)/i.test(response.url())) {
      scriptResponses.push({ url: response.url(), status: response.status() });
    }
  });

  page.on("request", request => {
    if (API_PATTERN.test(new URL(request.url()).pathname) && request.method() === "POST") {
      browserEvents.push({ kind: "api-post", url: request.url() });
    }
  });
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
    // Arm the request waiter BEFORE the click so a fast request cannot be
    // missed between the click and waiter registration.
    const requestWaiter = page.waitForRequest(request =>
      API_PATTERN.test(new URL(request.url()).pathname) && request.method() === "POST",
      { timeout: 15_000 }
    ).then(request => ({ request, error: null }), error => ({ request: null, error }));
    try {
      let clickError = null;
      try {
        await button.click({ timeout: 10_000 });
      } catch (error) {
        clickError = error.message;
      }
      let requestSeen = false;
      if (!clickError) {
        const waited = await requestWaiter;
        if (waited.request) {
          requestSeen = true;
        } else {
          clickError = "click completed but no POST /api/query was observed within 15 seconds: " + waited.error.message;
        }
      }
      if (!requestSeen) {
        const state = await page.evaluate(({ index }) => {
          const form = Array.from(document.querySelectorAll("form#archive-search-form"))[index];
          const root = form?.closest('.archive-stage-wrapper[data-guide-instance="woody"]');
          const button = form?.querySelector("#archive-submit-btn");
          const input = form?.querySelector("#archive-query-input");
          return {
            formFound: Boolean(form),
            inputValueLength: input?.value?.length ?? null,
            buttonDisabled: button?.disabled ?? null,
            buttonClass: button?.className ?? null,
            buttonLabel: button?.innerText ?? null,
            formControllerInstalled: form?.dataset?.useGuideControllerInstalled ?? null,
            rootControllerLoaded: root?.dataset?.useScopedControllerLoaded ?? null,
            rootControllerBuild: root?.__USE_GUIDE_FRONTEND_CONTROLLER__?.build ?? null,
            rootControllerAuthority: root?.__USE_GUIDE_FRONTEND_CONTROLLER__?.authority ?? null,
            rootExists: Boolean(root),
            scripts: Array.from(document.scripts).map(script => ({ src: script.src, type: script.type || "classic" })),
            listenerTrace: window.__guideE2EListenerTrace || []
          };
        }, { index });
        state.scriptResponses = scriptResponses;
        state.observedEvents = browserEvents;
        throw new Error(kind + " entryway did not submit. Browser state=" +
          JSON.stringify(state) + "; pageErrors=" + JSON.stringify(pageErrors) +
          "; consoleErrors=" + JSON.stringify(consoleErrors) +
          "; cause=" + clickError);
      }
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
