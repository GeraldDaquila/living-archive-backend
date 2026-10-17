import { chromium } from "playwright";

const GUIDE_URL = "https://geralddaquila.com/the-guide-find-your-way2/";
const QUERY = "What does stewardship mean in everyday life, and why does it matter now more than ever?";
const API_PATTERN = /\/api\/query(?:\?|$)/;
const mark = (stage, details = {}) => console.log(JSON.stringify({ stage, at: new Date().toISOString(), ...details }));

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
const page = await context.newPage();
page.setDefaultTimeout(8_000);
page.setDefaultNavigationTimeout(25_000);

const pageErrors = [];
const consoleErrors = [];
const eventTrace = [];
const scriptResponses = [];
const scriptFailures = [];
const posts = [];

page.on("pageerror", error => {
  pageErrors.push(error.message);
  mark("page_error", { message: error.message });
});
page.on("console", message => {
  const line = message.text();
  if (line.startsWith("GUIDE_CLICK_TRACE ")) {
    const item = line.slice("GUIDE_CLICK_TRACE ".length);
    eventTrace.push(item);
    mark("click_trace", { item });
  }
  if (message.type() === "error") consoleErrors.push(line);
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

/*
 * Install tracing before the page's own scripts. If a synchronous event handler
 * blocks the renderer, the last trace tells us how far click propagation got.
 * No production page or snippet is changed by this instrumentation.
 */
await page.addInitScript(() => {
  const trace = label => event => {
    if (event.type !== "click" || !event.target?.closest?.(".archive-stage-wrapper[data-guide-instance='woody']")) return;
    console.log("GUIDE_CLICK_TRACE " + JSON.stringify({
      label,
      phase: event.eventPhase,
      target: event.target?.id || event.target?.tagName || null,
      defaultPrevented: event.defaultPrevented,
      time: performance.now()
    }));
  };
  window.addEventListener("click", trace("window-capture"), true);
  document.addEventListener("click", trace("document-capture-early"), true);
  document.addEventListener("click", trace("document-bubble-early"), false);

  const bindNodeTrace = () => {
    const root = document.querySelector(".archive-stage-wrapper[data-guide-instance='woody']");
    if (!root || root.dataset.__clickTraceBound === "1") return;
    root.dataset.__clickTraceBound = "1";
    root.addEventListener("click", trace("root-capture-early"), true);
    root.addEventListener("click", trace("root-bubble-early"), false);
    const form = root.querySelector("#archive-search-form");
    const button = root.querySelector("#archive-submit-btn");
    form?.addEventListener("click", trace("form-capture-early"), true);
    form?.addEventListener("click", trace("form-bubble-early"), false);
    button?.addEventListener("click", trace("button-capture-early"), true);
    button?.addEventListener("click", trace("button-bubble-early"), false);
    console.log("GUIDE_CLICK_TRACE " + JSON.stringify({ label: "trace-listeners-installed", form: Boolean(form), button: Boolean(button) }));
  };
  new MutationObserver(bindNodeTrace).observe(document, { childList: true, subtree: true });
  if (document.readyState !== "loading") bindNodeTrace();
  document.addEventListener("DOMContentLoaded", bindNodeTrace, { once: true });
});

async function diagnostics() {
  return page.evaluate(() => {
    const root = document.querySelector(".archive-stage-wrapper[data-guide-instance='woody']");
    const form = root?.querySelector("form#archive-search-form");
    const button = form?.querySelector("#archive-submit-btn");
    const input = form?.querySelector("#archive-query-input");
    const ids = ["archive-stage-wrapper", "archive-search-form", "archive-submit-btn", "archive-query-input", "archive-response-box", "archive-response-text"];
    const duplicateIds = Object.fromEntries(ids.map(id => [id, document.querySelectorAll("#" + id).length]).filter(([, count]) => count > 1));
    return {
      title: document.title,
      rootFound: Boolean(root),
      rootAttributes: root ? Object.fromEntries(Array.from(root.attributes).map(a => [a.name, a.value])) : null,
      formFound: Boolean(form),
      inputLength: input?.value?.length ?? null,
      buttonDisabled: button?.disabled ?? null,
      buttonText: button?.innerText ?? null,
      formOnsubmitAttribute: form?.getAttribute("onsubmit") ?? null,
      duplicateIds,
      controllerFlags: root ? {
        submit: root.__USE_GUIDE_DELEGATED_SUBMIT_CONTROLLER__ ?? null,
        frontend: root.__USE_GUIDE_FRONTEND_CONTROLLER__ ?? null,
        safetyRootFlag: root.__USE_SAFETY_FOLLOWUP_CONTROLLER__ ?? null
      } : null,
      scripts: Array.from(document.scripts).map(s => s.src).filter(Boolean).filter(src => /guide|living-archive/i.test(src))
    };
  });
}

try {
  mark("navigation_start", { url: GUIDE_URL });
  await page.goto(GUIDE_URL, { waitUntil: "domcontentloaded", timeout: 25_000 });
  mark("navigation_complete", { title: await page.title() });

  const woody = page.locator(".archive-stage-wrapper[data-guide-instance='woody']");
  await woody.waitFor({ state: "attached", timeout: 8_000 });
  const form = woody.locator("form#archive-search-form").first();
  const input = form.locator("#archive-query-input").first();
  const button = form.locator("#archive-submit-btn").first();
  await input.fill(QUERY);

  const preClick = await diagnostics();
  mark("pre_click_diagnostic", preClick);

  const clickPromise = button.click({ timeout: 5_000 }).then(
    () => ({ kind: "click_completed" }),
    error => ({ kind: "click_error", message: error.message })
  );
  const clickOutcome = await Promise.race([
    clickPromise,
    new Promise(resolve => setTimeout(() => resolve({ kind: "click_watchdog_5s" }), 5_000))
  ]);
  mark("click_outcome", { ...clickOutcome, eventTraceCount: eventTrace.length });

  if (clickOutcome.kind === "click_watchdog_5s" || clickOutcome.kind === "click_error") {
    mark("diagnostic_stop_no_renderer_eval", {
      reason: "Avoid issuing another page.evaluate if click handling may have blocked the renderer.",
      eventTrace,
      posts,
      scriptResponses,
      scriptFailures,
      pageErrors,
      consoleErrors
    });
    process.exit(1);
  } else {
    const requestOutcome = await Promise.race([
      page.waitForRequest(request => request.method() === "POST" && API_PATTERN.test(new URL(request.url()).pathname), { timeout: 12_000 })
        .then(request => ({ kind: "post_observed", url: request.url() }))
        .catch(error => ({ kind: "no_post", message: error.message })),
      new Promise(resolve => setTimeout(() => resolve({ kind: "post_watchdog_12s" }), 12_000))
    ]);
    mark("request_outcome", { ...requestOutcome, postsObserved: posts.length });
    if (requestOutcome.kind !== "post_observed") process.exitCode = 1;
  }
} catch (error) {
  process.exitCode = 1;
  mark("diagnostic_failed", { message: error.message, eventTrace, posts, scriptResponses, scriptFailures, pageErrors, consoleErrors });
} finally {
  const closeResult = await Promise.race([
    browser.close().then(() => "closed", error => "close_error:" + error.message),
    new Promise(resolve => setTimeout(() => resolve("close_watchdog_3s"), 3_000))
  ]);
  mark("browser_close", { result: closeResult });
}
