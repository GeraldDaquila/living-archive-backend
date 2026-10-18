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
const cdpRequestUrls = new Map();
const cdpRequestMethods = new Map();
const apiRequestIds = new Set();
const apiResponseBodies = [];

// Chromium DevTools Protocol observes network events independently of the
// page's JavaScript event loop. Keep requestId→URL correlation because
// loadingFinished/loadingFailed events contain requestId but no URL.
const cdp = await context.newCDPSession(page);
await cdp.send("Network.enable");
for (const eventName of ["Network.requestWillBeSent", "Network.responseReceived", "Network.loadingFinished", "Network.loadingFailed"]) {
  cdp.on(eventName, async event => {
    const url = event.request?.url || event.response?.url || cdpRequestUrls.get(event.requestId) || "";
    if (eventName === "Network.requestWillBeSent" && url) {
      cdpRequestUrls.set(event.requestId, url);
      cdpRequestMethods.set(event.requestId, event.request?.method || "");
    }
    let pathname = "";
    try { pathname = new URL(url).pathname; } catch {}
    const method = event.request?.method || cdpRequestMethods.get(event.requestId) || "";
    if (API_PATTERN.test(pathname) && method === "POST") apiRequestIds.add(event.requestId);
    if (!API_PATTERN.test(pathname) && !apiRequestIds.has(event.requestId)) return;
    const item = {
      event: eventName,
      requestId: event.requestId,
      url: url || null,
      method: event.request?.method || cdpRequestMethods.get(event.requestId),
      status: event.response?.status,
      errorText: event.errorText,
      encodedDataLength: event.encodedDataLength,
      timestamp: event.timestamp
    };
    apiLifecycle.push(item);
    mark("cdp_api_lifecycle", item);
    if (eventName === "Network.loadingFinished" && apiRequestIds.has(event.requestId)) {
      try {
        const body = await cdp.send("Network.getResponseBody", { requestId: event.requestId });
        const bodyText = body.base64Encoded ? Buffer.from(body.body, "base64").toString("utf8") : body.body;
        const bodyRecord = {
          requestId: event.requestId,
          url: cdpRequestUrls.get(event.requestId) || null,
          bodyChars: bodyText.length,
          bodyPreview: bodyText.slice(0, 300)
        };
        apiResponseBodies.push(bodyRecord);
        mark("cdp_api_response_body", bodyRecord);
      } catch (error) {
        const bodyRecord = { requestId: event.requestId, error: error.message };
        apiResponseBodies.push(bodyRecord);
        mark("cdp_api_response_body_error", bodyRecord);
      }
    }
  });
}
// ExtraInfo carries the actual CORS response headers and any browser-side
// status code even when page-level response callbacks never fire.
for (const eventName of ["Network.requestWillBeSentExtraInfo", "Network.responseReceivedExtraInfo"]) {
  cdp.on(eventName, event => {
    const headers = event.headers || {};
    const requestUrl = cdpRequestUrls.get(event.requestId) || "";
    const requestMethod = cdpRequestMethods.get(event.requestId) || "";
    let requestPath = "";
    try { requestPath = new URL(requestUrl).pathname; } catch {}
    const isGuideApi = /\/api\/query(?:\?|$)/.test(requestPath);
    const isGuideApiExtra = isGuideApi || apiRequestIds.has(event.requestId);
    if (!isGuideApiExtra) return;
    const item = {
      event: eventName,
      requestId: event.requestId,
      url: requestUrl || null,
      method: requestMethod || null,
      statusCode: event.statusCode,
      headers: Object.fromEntries(Object.entries(headers).filter(([k]) => /access-control|content-type|content-length|vary|origin|x-render-origin-server|allow|method/i.test(k))),
      associatedCookies: event.associatedCookies?.length
    };
    apiLifecycle.push(item);
    mark("cdp_api_extra_info", item);
  });
}

page.on("requestfinished", request => {
  if (request.method() === "POST" && API_PATTERN.test(new URL(request.url()).pathname)) mark("api_request_finished", { url: request.url(), method: request.method() });
});
page.on("requestfailed", request => {
  if (request.method() === "POST" && API_PATTERN.test(new URL(request.url()).pathname)) mark("api_request_failed", { url: request.url(), method: request.method(), error: request.failure()?.errorText || "unknown" });
});

page.on("pageerror", error => {
  pageErrors.push(error.message);
  mark("page_error", { message: error.message });
});
page.on("console", message => {
  const line = message.text();
  if (line.startsWith("GUIDE_CLEANUP_OBSERVER_ISOLATION ")) {
    mark("cleanup_observer_isolation", { item: line.slice("GUIDE_CLEANUP_OBSERVER_ISOLATION ".length) });
  }
  if (line.startsWith("GUIDE_DYNAMIC_SCRIPT ")) {
    mark("dynamic_script_insertion", { item: line.slice("GUIDE_DYNAMIC_SCRIPT ".length) });
  }
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
  if (response.request().method() === "POST" && API_PATTERN.test(new URL(response.url()).pathname)) {
    apiResponses.push({ url: response.url(), method: response.request().method(), status: response.status() });
    mark("api_response_observed", { url: response.url(), method: response.request().method(), status: response.status() });
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
  // QA-only isolation: identify the text-cleanup MutationObserver by callback
  // source and suppress only its repeated observer callback. The script's
  // initial cleanAnswer() invocation still runs. This is not a production edit.
  const NativeMutationObserver = window.MutationObserver;
  window.MutationObserver = class GuideQaMutationObserver extends NativeMutationObserver {
    constructor(callback) {
      const callbackSource = String(callback);
      const isGuideCleanup = callback.name === "cleanAnswer" ||
        (callbackSource.includes("archive-response-text") &&
         callbackSource.includes("Stewardship Readiness") &&
         callbackSource.includes("nodeValue"));
      super(isGuideCleanup ? function guideQaCleanupObserverSuppressed() {} : callback);
      if (isGuideCleanup) {
        console.log("GUIDE_CLEANUP_OBSERVER_ISOLATION " + JSON.stringify({
          callbackName: callback.name || null,
          callbackSourcePreview: callbackSource.slice(0, 180),
          suppressed: true
        }));
      }
    }
  };
  // Identify who dynamically installs the data-URL cleanAnswer script seen in
  // the call stack. QA-only instrumentation; no production source is changed.
  const reportDynamicScript = (node, operation) => {
    try {
      if (node?.tagName !== "SCRIPT") return;
      const src = String(node.src || "");
      const prefix = "data:text/javascript;base64,";
      if (!src.startsWith(prefix)) return;
      let source = "";
      try {
        const binary = atob(src.slice(prefix.length));
        const bytes = Uint8Array.from(binary, character => character.charCodeAt(0));
        source = new TextDecoder().decode(bytes);
      } catch {}
      let candidatePatched = false;
      const unsafeWrite = "node.nodeValue = value.replace(titleMarker, '');";
      if (source.includes("function cleanAnswer") && source.includes("titleMarker") && source.includes(unsafeWrite)) {
        source = source.replace(
          unsafeWrite,
          "var cleanedValue = value.replace(titleMarker, '');\n      if (cleanedValue !== value) node.nodeValue = cleanedValue;"
        );
        const bytes = new TextEncoder().encode(source);
        let binary = "";
        for (const byte of bytes) binary += String.fromCharCode(byte);
        node.src = prefix + btoa(binary);
        candidatePatched = true;
      }
      console.log("GUIDE_DYNAMIC_SCRIPT " + JSON.stringify({
        operation,
        srcPrefix: String(node.src).slice(0, 180),
        candidatePatched,
        stack: new Error("Guide dynamic script insertion").stack
      }));
    } catch {}
  };
  const originalAppendChild = Node.prototype.appendChild;
  Node.prototype.appendChild = function(node) {
    reportDynamicScript(node, "appendChild");
    return originalAppendChild.call(this, node);
  };
  const originalInsertBefore = Node.prototype.insertBefore;
  Node.prototype.insertBefore = function(node, referenceNode) {
    reportDynamicScript(node, "insertBefore");
    return originalInsertBefore.call(this, node, referenceNode);
  };
  const originalSetAttribute = Element.prototype.setAttribute;
  Element.prototype.setAttribute = function(name, value) {
    if (this.tagName === "SCRIPT" && String(name).toLowerCase() === "src" && String(value).startsWith("data:text/javascript")) {
      console.log("GUIDE_DYNAMIC_SCRIPT " + JSON.stringify({
        operation: "setAttribute-src",
        srcPrefix: String(value).slice(0, 180),
        stack: new Error("Guide dynamic script src").stack
      }));
    }
    return originalSetAttribute.call(this, name, value);
  };

  // Trace synchronous entry into the Woody controller's DOM and async boundaries.
  // Bounded counters prevent diagnostic output from overwhelming the runner.
  const originalGetElementById = Document.prototype.getElementById;
  let lookupTraceCount = 0;
  let responseTextStackCount = 0;
  Document.prototype.getElementById = function (id) {
    const normalizedId = String(id);
    if (normalizedId === "archive-response-text" && responseTextStackCount++ < 5) {
      console.log("GUIDE_EXEC_TRACE " + JSON.stringify({
        stage: "response_text_lookup_stack",
        id: normalizedId,
        time: performance.now(),
        stack: new Error("Guide response-text lookup").stack
      }));
    } else if (lookupTraceCount++ < 10) {
      console.log("GUIDE_EXEC_TRACE " + JSON.stringify({ stage: "getElementById", id: normalizedId, time: performance.now() }));
    }
    return originalGetElementById.call(this, id);
  };
  const originalRAF = window.requestAnimationFrame.bind(window);
  let rafTraceCount = 0;
  window.requestAnimationFrame = callback => originalRAF(timestamp => {
    // Keep this instrumentation bounded: never emit a console record per frame.
    if (rafTraceCount++ < 5) {
      console.log("GUIDE_EXEC_TRACE " + JSON.stringify({ stage: "animation_frame_enter", time: performance.now() }));
    }
    callback(timestamp);
  });
  const originalFetch = window.fetch.bind(window);
  window.fetch = (...args) => {
    const url = String(args[0]);
    console.log("GUIDE_EXEC_TRACE " + JSON.stringify({ stage: "fetch_enter", url, time: performance.now() }));
    return originalFetch(...args).then(response => {
      if (/\/api\/query(?:\?|$)/.test(url)) {
        console.log("GUIDE_EXEC_TRACE " + JSON.stringify({
          stage: "fetch_resolved", url, status: response.status, ok: response.ok, time: performance.now()
        }));
      }
      return response;
    }).catch(error => {
      console.log("GUIDE_EXEC_TRACE " + JSON.stringify({
        stage: "fetch_rejected", url, name: error?.name || null, message: error?.message || String(error), time: performance.now()
      }));
      throw error;
    });
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

// QA-only fault isolation: if the live HTML contains the deployed
// title-cleanup script, patch only the test response so we can verify whether
// its unconditional text-node writes are the cause. WordPress is not modified.
await page.route("https://geralddaquila.com/the-guide-find-your-way2/", async route => {
  const response = await route.fetch();
  const html = await response.text();
  let replacements = 0;
  const patchedHtml = html.replace(/src=["']data:text\/javascript;base64,([^"']+)["']/g, (whole, encoded) => {
    let source;
    try { source = Buffer.from(encoded, "base64").toString("utf8"); }
    catch { return whole; }
    if (!source.includes("function cleanAnswer") ||
        !source.includes("titleMarker") ||
        !source.includes("node.nodeValue = value.replace(titleMarker, '')")) return whole;
    source = source.replace(
      "node.nodeValue = value.replace(titleMarker, '');",
      "var cleanedValue = value.replace(titleMarker, '');\n      if (cleanedValue !== value) node.nodeValue = cleanedValue;"
    );
    replacements += 1;
    return whole.replace(encoded, Buffer.from(source, "utf8").toString("base64"));
  });
  mark("qa_html_fault_isolation", {
    url: route.request().url(),
    bodyLength: html.length,
    hasWoodyRoot: html.includes("archive-stage-wrapper"),
    hasInlineCleanup: html.includes("titleMarker"),
    patchedCleanupScriptCount: replacements
  });
  const headers = { ...response.headers() };
  delete headers["content-encoding"];
  delete headers["content-length"];
  delete headers["etag"];
  await route.fulfill({ status: response.status(), headers, body: patchedHtml });
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
    response => response.request().method() === "POST" && API_PATTERN.test(new URL(response.url()).pathname),
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
    mark("diagnostic_grace_period_started", {
      reason: "No POST observed yet; continue collecting network and renderer evidence instead of terminating."
    });
    const graceOutcome = await Promise.race([
      new Promise(resolve => setTimeout(() => resolve({ kind: "grace_elapsed_15s" }), 15_000)),
      page.waitForRequest(request => request.method() === "POST" && API_PATTERN.test(new URL(request.url()).pathname), { timeout: 15_000 })
        .then(request => ({ kind: "post_observed_during_grace", url: request.url() }))
        .catch(() => ({ kind: "no_post_during_grace" }))
    ]);
    mark("diagnostic_grace_period_result", { ...graceOutcome, posts, apiLifecycle, pageErrors, consoleErrors });
    const graceRendererProbe = await Promise.race([
      page.evaluate(() => ({
        readyState: document.readyState,
        activeElement: document.activeElement?.id || document.activeElement?.tagName || null,
        buttonDisabled: document.querySelector(".archive-stage-wrapper[data-guide-instance='woody'] #archive-submit-btn")?.disabled ?? null,
        responseTextLength: document.querySelector(".archive-stage-wrapper[data-guide-instance='woody'] #archive-response-text")?.innerText?.trim()?.length ?? null,
        now: performance.now()
      })).then(value => ({ kind: "renderer_responsive", value })),
      new Promise(resolve => setTimeout(() => resolve({ kind: "renderer_probe_timeout_5s" }), 5_000))
    ]);
    mark("grace_renderer_probe", { result: graceRendererProbe, apiLifecycle, posts, apiResponses });
    if (cpuProfileStarted) {
      const profileResult = await Promise.race([
        cdp.send("Profiler.stop").then(result => ({ kind: "profile_captured", profile: result.profile })),
        new Promise(resolve => setTimeout(() => resolve({ kind: "profile_stop_timeout_5s" }), 5_000))
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
        mark("no_post_cpu_profile_summary", {
          durationSeconds: ((profile.endTime || 0) - (profile.startTime || 0)) / 1_000_000,
          sampleCount: profile.samples?.length || 0,
          topNodes: nodes
        });
      } else {
        mark("no_post_cpu_profile_summary", { kind: profileResult.kind });
      }
    }
    mark("diagnostic_no_request_final", {
      reason: "No API POST was observed after the 15-second evidence-collection window.",
      clickOutcome, eventTrace, posts, apiResponses, apiLifecycle, apiResponseBodies,
      scriptResponses, scriptFailures, pageErrors, consoleErrors
    });
    process.exitCode = 1;
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
    mark("response_outcome", { ...responseOutcome, apiResponses, apiLifecycle, apiResponseBodies });

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
