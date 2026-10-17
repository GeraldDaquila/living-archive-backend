// Diagnostic rerun marker: 2026-10-18; QA branch only, no production changes.
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
const apiResponses = [];
const apiLifecycle = [];

// Chromium DevTools Protocol observes network events independently of the
// page's JavaScript event loop. This distinguishes renderer stalls from
// requests that genuinely never receive/finish a response.
const cdp = await context.newCDPSession(page);
await cdp.send("Network.enable");
for (const eventName of ["Network.requestWillBeSent", "Network.responseReceived", "Network.loadingFinished", "Network.loadingFailed"]) {
  cdp.on(eventName, event => {
    const url = event.request?.url || event.response?.url || "";
    let pathname = "";
    try { pathname = new URL(url).pathname; } catch {}
    if (!API_PATTERN.test(pathname)) return;
    const item = {
      event: eventName,
      requestId: event.requestId,
      url,
      method: event.request?.method,
      status: event.response?.status,
      errorText: event.errorText,
      timestamp: event.timestamp
    };
    apiLifecycle.push(item);
    mark("cdp_api_lifecycle", item);
  });
}
// ExtraInfo carries the actual CORS response headers and any browser-side
// status code even when page-level response callbacks never fire.
for (const eventName of ["Network.requestWillBeSentExtraInfo", "Network.responseReceivedExtraInfo"]) {
  cdp.on(eventName, event => {
    const item = {
      event: eventName,
      requestId: event.requestId,
      statusCode: event.statusCode,
      headers: event.headers ? Object.fromEntries(Object.entries(event.headers).filter(([k]) => /access-control|content-type|content-length|vary|origin/i.test(k))) : undefined,
      associatedCookies: event.associatedCookies?.length
    };
    apiLifecycle.push(item);
    mark("cdp_api_extra_info", item);
  });
}

page.on("requestfinished", request => {
  if (API_PATTERN.test(new URL(request.url()).pathname)) mark("api_request_finished", { url: request.url() });
});
page.on("requestfailed", request => {
  if (API_PATTERN.test(new URL(request.url()).pathname)) mark("api_request_failed", { url: request.url(), error: request.failure()?.errorText || "unknown" });
});

page.on("pageerror", error => {
  pageErrors.push(error.message);
  mark("page_error", { message: error.message });
});
page.on("console", message => {
  const line = message.text();
  if (line.startsWith("GUIDE_EXEC_TRACE ")) {
    const item = line.slice("GUIDE_EXEC_TRACE ".length);
    mark("execution_trace", { item });
  }
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
  if (API_PATTERN.test(new URL(response.url()).pathname)) {
    apiResponses.push({ url: response.url(), status: response.status() });
    mark("api_response_observed", { url: response.url(), status: response.status() });
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
  // Trace synchronous entry into the Woody controller's DOM and async boundaries.
  // Bounded counters prevent diagnostic output from overwhelming the runner.
  const originalGetElementById = Document.prototype.getElementById;
  let lookupTraceCount = 0;
  Document.prototype.getElementById = function (id) {
    if (lookupTraceCount++ < 35) {
      console.log("GUIDE_EXEC_TRACE " + JSON.stringify({ stage: "getElementById", id: String(id), time: performance.now() }));
    }
    return originalGetElementById.call(this, id);
  };
  const originalRAF = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = callback => originalRAF(timestamp => {
    console.log("GUIDE_EXEC_TRACE " + JSON.stringify({ stage: "animation_frame_enter", time: performance.now() }));
    callback(timestamp);
  });
  const originalFetch = window.fetch.bind(window);
  window.fetch = (...args) => {
    console.log("GUIDE_EXEC_TRACE " + JSON.stringify({ stage: "fetch_enter", url: String(args[0]), time: performance.now() }));
    return originalFetch(...args);
  };
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

  // QA-only CPU profile: capture the renderer's sampled JavaScript stack during the freeze.
  // CDP operates outside page.evaluate, so this can still help when the page event loop stalls.
  let cpuProfileStarted = false;
  try {
    await cdp.send("Profiler.enable");
    await cdp.send("Profiler.setSamplingInterval", { interval: 10_000 });
    await cdp.send("Profiler.start");
    cpuProfileStarted = true;
    mark("cpu_profile_started", { samplingIntervalMicroseconds: 10_000 });
  } catch (error) {
    mark("cpu_profile_start_failed", { message: error.message });
  }

  // Arm the response listener BEFORE clicking. A fast response may arrive
  // before the click promise settles; registering after the click loses it.
  const responsePromise = page.waitForResponse(
    response => API_PATTERN.test(new URL(response.url()).pathname),
    { timeout: 35_000 }
  ).then(response => ({ kind: "response_observed", url: response.url(), status: response.status() }))
   .catch(error => ({ kind: "no_response", message: error.message }));

  const clickPromise = button.click({ timeout: 5_000 }).then(
    () => ({ kind: "click_completed" }),
    error => ({ kind: "click_error", message: error.message })
  );
  const clickOutcome = await Promise.race([
    clickPromise,
    new Promise(resolve => setTimeout(() => resolve({ kind: "click_watchdog_5s" }), 5_000))
  ]);
  mark("click_outcome", { ...clickOutcome, eventTraceCount: eventTrace.length });

  // A click timeout is not itself a submission failure: the capture handler can
  // dispatch the request and mutate the button before Playwright finishes its click.
  // Continue only when a real POST was observed; otherwise preserve the fail-closed stop.
  if ((clickOutcome.kind === "click_watchdog_5s" || clickOutcome.kind === "click_error") && posts.length === 0) {
    mark("diagnostic_stop_no_request", {
      reason: "Click did not complete and no API POST was observed.",
      eventTrace, posts, apiResponses, scriptResponses, scriptFailures, pageErrors, consoleErrors
    });
    process.exit(1);
  }

  const requestOutcome = posts.length
    ? { kind: "post_observed", url: posts[0].url }
    : await Promise.race([
        page.waitForRequest(request => request.method() === "POST" && API_PATTERN.test(new URL(request.url()).pathname), { timeout: 12_000 })
          .then(request => ({ kind: "post_observed", url: request.url() }))
          .catch(error => ({ kind: "no_post", message: error.message })),
        new Promise(resolve => setTimeout(() => resolve({ kind: "post_watchdog_12s" }), 12_000))
      ]);
  mark("request_outcome", { ...requestOutcome, postsObserved: posts.length });

  if (requestOutcome.kind === "post_observed") {
    const responseOutcome = await Promise.race([
      responsePromise,
      new Promise(resolve => setTimeout(() => resolve({ kind: "response_watchdog_35s" }), 35_000))
    ]);
    mark("response_outcome", { ...responseOutcome, apiResponses, apiLifecycle });

    // Probe renderer responsiveness without making it a gate for collecting
    // network evidence. A timeout is diagnostic, not a new production claim.
    const rendererProbe = await Promise.race([
      page.evaluate(() => ({
        readyState: document.readyState,
        responseTextLength: document.querySelector(".archive-stage-wrapper[data-guide-instance='woody'] #archive-response-text")?.innerText?.trim()?.length ?? null,
        now: performance.now()
      })).then(value => ({ kind: "renderer_responsive", value })),
      new Promise(resolve => setTimeout(() => resolve({ kind: "renderer_probe_timeout" }), 3_000))
    ]);
    mark("renderer_probe", { rendererProbe, apiLifecycle });

    const uiOutcome = await Promise.race([
      page.waitForFunction(() => {
        const root = document.querySelector(".archive-stage-wrapper[data-guide-instance='woody']");
        const box = root?.querySelector("#archive-response-box");
        const text = root?.querySelector("#archive-response-text");
        const content = (text?.innerText || box?.innerText || "").trim();
        return content.length > 80;
      }, null, { timeout: 15_000 }).then(() => ({ kind: "response_ui_present" }))
        .catch(error => ({ kind: "response_ui_missing", message: error.message })),
      new Promise(resolve => setTimeout(() => resolve({ kind: "ui_watchdog_15s" }), 15_000))
    ]);
    mark("ui_outcome", { ...uiOutcome });
    if (cpuProfileStarted) {
      const profileResult = await Promise.race([
        cdp.send("Profiler.stop").then(result => ({ kind: "profile_captured", profile: result.profile })),
        new Promise(resolve => setTimeout(() => resolve({ kind: "profile_stop_timeout" }), 5_000))
      ]);
      if (profileResult.kind === "profile_captured") {
        const profile = profileResult.profile;
        const nodes = (profile.nodes || []).map(node => ({
          functionName: node.callFrame?.functionName || "(anonymous)",
          url: node.callFrame?.url || "",
          lineNumber: node.callFrame?.lineNumber,
          columnNumber: node.callFrame?.columnNumber,
          selfSamples: node.hitCount || 0,
          children: node.children?.length || 0
        })).sort((a, b) => b.selfSamples - a.selfSamples).slice(0, 30);
        mark("cpu_profile_summary", {
          kind: profileResult.kind,
          durationSeconds: ((profile.endTime || 0) - (profile.startTime || 0)) / 1_000_000,
          sampleCount: profile.samples?.length || 0,
          topNodes: nodes
        });
      } else {
        mark("cpu_profile_summary", { kind: profileResult.kind });
      }
    }
    const finalDiagnostics = await diagnostics().catch(error => ({ diagnosticError: error.message }));
    mark("final_diagnostic", { finalDiagnostics, posts, apiResponses, pageErrors, consoleErrors });
    if (responseOutcome.kind !== "response_observed" || responseOutcome.status < 200 || responseOutcome.status >= 300 || uiOutcome.kind !== "response_ui_present") process.exitCode = 1;
  } else {
    process.exitCode = 1;
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
