import { chromium } from "playwright";

const GUIDE_URL = "https://geralddaquila.com/the-guide-find-your-way2/?qa_live=healthy-community-20261022";
const PRIMARY_API_ORIGIN = "https://living-archive-backend.onrender.com";
const MIRROR_API_ORIGIN = "https://living-archive-backend-mirror.onrender.com";
const BACKEND_API_ORIGINS = [PRIMARY_API_ORIGIN, MIRROR_API_ORIGIN];
const USE_API_ORIGIN = (process.env.USE_API_ORIGIN || PRIMARY_API_ORIGIN).replace(/\/+$/, "");
const EXPECTED_USE_VERSION = (process.env.EXPECTED_USE_VERSION || "").trim();
const QUERY = "I'm new to the Living Archive. I care about healthier communities, but I don't know its vocabulary or where to begin.";
const EXPECTED_TITLE = "What Healthy Communities Actually Look Like";
const EXPECTED_URL = "https://geralddaquila.com/2025/10/07/t4-codex-overflow-communities-governance-by-resonance/";
const ROOT = ".archive-stage-wrapper[data-guide-instance='woody']";

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ serviceWorkers: "block" });
const page = await context.newPage();
page.setDefaultTimeout(60_000);
page.setDefaultNavigationTimeout(30_000);

// The WordPress controller points at production. For PR acceptance, route its
// real browser requests to the isolated QA deployment of this exact candidate.
if (USE_API_ORIGIN !== PRIMARY_API_ORIGIN) {
  await page.route("**/api/query", async route => {
    const requestedUrl = route.request().url();
    const sourceOrigin = BACKEND_API_ORIGINS.find(origin =>
      requestedUrl.startsWith(origin + "/api/query")
    );
    if (!sourceOrigin || sourceOrigin === USE_API_ORIGIN) {
      await route.continue();
      return;
    }
    const targetUrl = USE_API_ORIGIN + requestedUrl.slice(sourceOrigin.length);
    // route.fetch() only obtains the upstream response; fulfill the browser's
    // intercepted request with it or the controller will time out and choose
    // the untouched mirror response instead.
    const upstreamResponse = await route.fetch({ url: targetUrl });
    await route.fulfill({ response: upstreamResponse });
  });
}

const startedAt = Date.now();
const elapsed = () => Date.now() - startedAt;
const apiRequests = [];
const apiResponses = [];
const apiBodyReads = [];
const apiFailures = [];
const apiFinished = [];
const pageErrors = [];
const consoleErrors = [];
page.on("pageerror", error => {
  pageErrors.push({ name: error.name || "Error", message: error.message, stack: error.stack || "" });
});
page.on("console", message => {
  if (message.type() === "error") {
    consoleErrors.push({ text: message.text(), location: message.location() });
  }
});
page.on("request", request => {
  if (request.method() === "POST" && request.url().includes("/api/query")) {
    let body = {};
    try { body = JSON.parse(request.postData() || "{}"); } catch {}
    apiRequests.push({ url: request.url(), body, atMs: elapsed() });
  }
});
page.on("response", response => {
  if (!response.url().includes("/api/query")) return;
  const record = { url: response.url(), status: response.status(), atMs: elapsed(), payload: null, bodyReadError: null };
  apiResponses.push(record);
  apiBodyReads.push(response.json().then(payload => { record.payload = payload; }).catch(error => { record.bodyReadError = error?.message || String(error); }));
});
page.on("requestfailed", request => {
  if (request.url().includes("/api/query")) {
    apiFailures.push({ url: request.url(), atMs: elapsed(), error: request.failure()?.errorText || "unknown" });
  }
});
page.on("requestfinished", request => {
  if (request.url().includes("/api/query")) {
    apiFinished.push({ url: request.url(), atMs: elapsed() });
  }
});

const controllerSyntaxDiagnostics = [];
let inlineScriptSyntaxDiagnostics = [];
let externalScriptSyntaxDiagnostics = [];

try {
  console.log(JSON.stringify({ stage: "live_e2e_start", url: GUIDE_URL }));
  page.on("response", async response => {
    if (/\/guide-controller-v\d+\.\d+\.js(?:\?|$)/.test(response.url())) {
      try {
        const source = await response.text();
        // Match the actual browser parse path: classic script parsing.
        new Function(source);
        console.log(JSON.stringify({ stage: "controller_source_syntax_ok", url: response.url(), sourceBytes: source.length }));
      } catch (error) {
        controllerSyntaxDiagnostics.push(JSON.stringify({ message: String(error && error.message || error), stack: String(error && error.stack || ""), url: response.url(), sourceBytes: source ? source.length : null }));
      }
    }
  });
  await page.goto(GUIDE_URL, { waitUntil: "domcontentloaded" });
  await page.waitForLoadState("load").catch(() => {});
  inlineScriptSyntaxDiagnostics = await page.locator("script:not([src])").evaluateAll(scripts =>
    scripts.map((script, index) => {
      const type = (script.getAttribute("type") || "text/javascript").toLowerCase();
      if (!["text/javascript", "application/javascript", "module", ""].includes(type)) return null;
      const source = script.textContent || "";
      if (!source.trim()) return null;
      try {
        new Function(source);
        return null;
      } catch (error) {
        return { index, type, id: script.id || null, bytes: source.length, message: error.message };
      }
    }).filter(Boolean)
  );
  externalScriptSyntaxDiagnostics = [];
  for (const script of await page.locator('script[src*="guide-controller"], script[src*="marked"]').evaluateAll(nodes => nodes.map(node => node.src))) {
    try {
      const response = await page.request.get(script);
      const source = await response.text();
      new Function(source);
    } catch (error) {
      externalScriptSyntaxDiagnostics.push({ url: script, message: error.message || String(error) });
    }
  }
  const root = page.locator(ROOT);
  await root.waitFor({ state: "attached" });
  const input = root.locator("#archive-query-input");
  const submit = root.locator("#archive-submit-btn");
  const answer = root.locator("#archive-response-text");
  await input.waitFor({ state: "visible" });
  await submit.waitFor({ state: "visible" });
  await input.fill(QUERY);

  // Use a DOM click so the test observes the actual live controller without
  // Playwright auto-waiting on a possible form navigation.
  await submit.evaluate(element => setTimeout(() => element.click(), 0));

  // The controller renders the canonical doorway in a sibling navigation surface,
  // not inside the substantive answer-text element.
  const link = root.locator("a.la-answer-doorway__link");
  try {
    await link.waitFor({ state: "visible", timeout: 60_000 });
  } catch (error) {
    await Promise.all(apiBodyReads);
    const diagnostics = {
      visibleAnswerText: await answer.innerText().catch(() => ""),
      answerHtml: await answer.evaluate(node => node.innerHTML.slice(0, 4000)).catch(() => ""),
      answerState: await answer.evaluate(node => ({
        display: getComputedStyle(node).display,
        visibility: getComputedStyle(node).visibility,
        opacity: getComputedStyle(node).opacity,
        rects: node.getClientRects().length,
        className: node.className
      })).catch(() => null),
      rootLinks: await root.locator("a").evaluateAll(nodes => nodes.map(node => ({
        text: (node.innerText || "").trim(),
        href: node.href,
        className: node.className,
        visible: Boolean(node.getClientRects().length)
      }))).catch(() => []),
      answerLinks: await answer.locator("a").evaluateAll(nodes => nodes.map(node => ({
        text: (node.innerText || "").trim(),
        href: node.href,
        className: node.className,
        visible: Boolean(node.getClientRects().length)
      }))).catch(() => []),
      rootText: await root.innerText().catch(() => ""),
      apiRequests,
      apiResponses: apiResponses.map(item => ({
        status: item.status,
        payloadQuery: item.payload?.query,
        response: typeof item.payload?.response === "string" ? item.payload.response.slice(0, 1800) : null,
        recommendation: item.payload?.recommendation || null,
        answerBasis: item.payload?.answer_basis || null,
        bodyReadError: item.bodyReadError
      })),
      apiFailures,
      apiFinished,
      pageErrors,
      consoleErrors,
      controllerSyntaxDiagnostics,
      inlineScriptSyntaxDiagnostics,
      externalScriptSyntaxDiagnostics,
      waitError: error.message
    };
    throw new Error(
      "The live backend response did not produce a visible visitor doorway link. " +
      JSON.stringify(diagnostics)
    );
  }
  const rendered = await link.evaluate(node => ({
    title: node.innerText.trim(),
    href: node.href,
    visible: Boolean(node.getClientRects().length)
  }));
  const responseText = await answer.innerText();
  // The link proves the UI rendered; now wait for the separately captured API
  // bodies before validating the response contract.
  await Promise.all(apiBodyReads);
  if (rendered.title !== EXPECTED_TITLE) {
    throw new Error("Live visitor link title mismatch: " + JSON.stringify(rendered));
  }
  if (rendered.href !== EXPECTED_URL) {
    throw new Error("Live visitor link URL mismatch: " + JSON.stringify(rendered));
  }
  if (!responseText.includes("A healthy community")) {
    throw new Error("The substantive answer was not rendered before the recommendation.");
  }
  if (!apiRequests.some(request => request.body.query === QUERY)) {
    throw new Error("No real production /api/query request carried the acceptance query.");
  }
  if (!apiResponses.some(item =>
    item.status === 200 &&
    item.payload?.recommendation?.title === EXPECTED_TITLE &&
    item.payload?.recommendation?.url === EXPECTED_URL
  )) {
    throw new Error("The real production API did not return the exact canonical recommendation pair.");
  }
  // Exact regression for the newly recovered stable general fact. This is
  // checked through the real WordPress UI and candidate API, not only with
  // source-text assertions.
  const waterQuery = "What is the boiling point of water at sea level?";
  await input.fill(waterQuery);
  await submit.evaluate(element => setTimeout(() => element.click(), 0));
  // Wait on the captured API payload first so an incorrect runtime response
  // fails with its actual body rather than timing out in the browser DOM.
  const waterDeadline = Date.now() + 45_000;
  while (
    !apiResponses.some(item => item.payload && item.payload.query === waterQuery) &&
    Date.now() < waterDeadline
  ) {
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  await Promise.all(apiBodyReads);
  const waterResponses = apiResponses.filter(item =>
    item.payload && item.payload.query === waterQuery
  );
  if (!apiRequests.some(request => request.body.query === waterQuery)) {
    throw new Error("No real WordPress /api/query request carried the exact boiling-point question.");
  }
  const waterResponse = waterResponses.find(item =>
    item.status === 200 &&
    typeof item.payload?.response === "string" &&
    /100\s*°?c/i.test(item.payload.response) &&
    /212\s*°?f/i.test(item.payload.response) &&
    /standard atmospheric pressure/i.test(item.payload.response) &&
    item.payload?.answer_basis?.kind === "general_knowledge" &&
    item.payload?.recommendation == null &&
    !/i haven.t found enough support|rather than fill the gap with outside knowledge/i.test(item.payload.response)
  );
  if (!waterResponse) {
    throw new Error("The exact boiling-point question did not return the general-fact contract without Archive-only refusal or an invented doorway. Responses: " +
      JSON.stringify(waterResponses.map(item => ({
        status: item.status,
        answer_basis: item.payload?.answer_basis,
        recommendation: item.payload?.recommendation,
        response: item.payload?.response
      }))));
  }
  const waterUI = (await answer.innerText()).replace(/\s+/g, " ").trim();
  const waterAPI = waterResponse.payload.response.replace(/\s+/g, " ").trim();
  if (!waterUI.toLowerCase().includes("100") ||
      !waterUI.toLowerCase().includes("212") ||
      !waterUI.toLowerCase().includes("pressure") ||
      waterUI.toLowerCase().includes("living archive's available material")) {
    throw new Error("The rendered visitor response did not match the concise general-fact boundary: " + waterUI);
  }
  if (await root.locator("a.la-answer-doorway__link").count() !== 0) {
    throw new Error("The boiling-point response displayed a doorway even though no relevant canonical resource was verified.");
  }
  if (!waterUI.includes(waterAPI.slice(0, Math.min(48, waterAPI.length)))) {
    throw new Error("The visible water answer did not reflect the candidate API response.");
  }

  // Exercise the exact conceptual question that previously fell through to the
  // evidence-limitation message despite canonical recovery passing. Keep this test
  // explicit about the trusted answer contract, rather than relying on query-word
  // overlap which could mistake the fallback itself for a satisfactory answer.
  const conceptualQuery = "What is the role of trust in community stewardship?";
  await input.fill(conceptualQuery);
  await submit.evaluate(element => setTimeout(() => element.click(), 0));
  try {
    await page.waitForFunction(() => {
      // The landing page can contain multiple historical Guide instances with
      // duplicate legacy IDs. Acceptance must inspect the active Woody instance,
      // not whichever #archive-response-text happens to appear first in the DOM.
      const root = document.querySelector(".archive-stage-wrapper[data-guide-instance='woody']");
      const el = root?.querySelector("#archive-response-text");
      const text = (el?.innerText || "").toLowerCase();
      return !!el && text.length > 100 && /trust/.test(text) && /community|stewardship/.test(text);
    }, null, { timeout: 60_000 });
  } catch (error) {
    await Promise.all(apiBodyReads);
    const conceptualDiagnostics = apiResponses
      .filter(item => item.payload && item.payload.query === conceptualQuery)
      .map(item => ({
        status: item.status,
        intent: item.payload?.intent,
        answer_basis: item.payload?.answer_basis,
        response: item.payload?.response,
        recommendation: item.payload?.recommendation
      }));
    const visibleText = await answer.innerText().catch(() => "");
    throw new Error(
      "Conceptual trust/stewardship response did not render in the active Woody instance. " +
      JSON.stringify({ visibleText, conceptualDiagnostics, pageErrors, inlineScriptSyntaxDiagnostics, externalScriptSyntaxDiagnostics, waitError: error.message })
    );
  }
  const conceptualText = await answer.innerText();
  await Promise.all(apiBodyReads);
  const conceptualResponses = apiResponses.filter(item =>
    item.payload && item.payload.query === conceptualQuery
  );
  if (!apiRequests.some(request => request.body.query === conceptualQuery)) {
    throw new Error("No real production /api/query request carried the conceptual trust/stewardship query.");
  }
  const supportedResponse = conceptualResponses.find(item =>
    item.status === 200 &&
    item.payload?.intent === "TOPICAL_INQUIRY" &&
    (!EXPECTED_USE_VERSION || item.payload?.version === EXPECTED_USE_VERSION) &&
    typeof item.payload?.response === "string" &&
    item.payload.response.trim().length >= 120 &&
    item.payload?.recommendation &&
    /^https:\/\/geralddaquila\.com\//i.test(item.payload.recommendation.url || "")
  );
  if (!supportedResponse) {
    throw new Error("Conceptual trust/stewardship question did not return an Archive-grounded answer and canonical recommendation. Responses: " +
      JSON.stringify(conceptualResponses.map(item => ({
        status:item.status,
        intent:item.payload?.intent,
        answer_basis:item.payload?.answer_basis,
        recommendation:item.payload?.recommendation,
        response:item.payload?.response
      }))));
  }
  const normalizedUI = conceptualText.replace(/\s+/g, " ").trim().toLowerCase();
  const normalizedAPI = supportedResponse.payload.response.replace(/\s+/g, " ").trim().toLowerCase();
  if (!normalizedAPI.split(/[.!?]+/).map(part=>part.trim()).filter(part=>part.length>20)
    .some(part=>normalizedUI.includes(part.slice(0, Math.min(part.length, 48))))) {
    throw new Error("The browser did not render a meaningful portion of the Archive-grounded API answer.");
  }
  // Acceptance is not complete merely because a long grounded answer rendered.
  // The provider-exhaustion path must retain The Guide's ordinary, patient voice.
  // These phrases are deliberate user-facing contract language, not a citation
  // shortcut: canonical-source evidence gates above still have to pass.
  const normalizedHumanVoice = normalizedAPI;
  for (const requiredPhrase of [
    "trust helps people in a community rely on one another",
    "think of a shared garden",
    "stewardship is tending the garden"
  ]) {
    if (!normalizedHumanVoice.includes(requiredPhrase)) {
      throw new Error("The conceptual fallback lost The Guide's required human voice. Missing phrase: " + requiredPhrase +
        ". Actual API response: " + supportedResponse.payload.response);
    }
  }
  for (const forbiddenPhrase of [
    "canonical source",
    "bounded synthesis",
    "not a claim that any one sentence",
    "verbatim"
  ]) {
    if (normalizedHumanVoice.includes(forbiddenPhrase)) {
      throw new Error("The conceptual fallback exposed audit-style or internal wording: " + forbiddenPhrase +
        ". Actual API response: " + supportedResponse.payload.response);
    }
  }
  if (/^[^\S\r\n]*[✨🌱🔹🔸✅⚠️]/mu.test(supportedResponse.payload.response)) {
    throw new Error("The conceptual fallback began a response line with decorative emoji.");
  }
  if (await root.locator("a.la-answer-doorway__link").count() !== 1) {
    throw new Error("The conceptual response must render exactly one canonical recommendation link.");
  }
  const conceptualLink = await root.locator("a.la-answer-doorway__link").first().evaluate(el=>({href:el.href,text:(el.innerText||el.textContent||"").trim()}));
  if (conceptualLink.href !== supportedResponse.payload.recommendation.url) {
    throw new Error("The conceptual recommendation URL does not match the API-selected canonical destination.");
  }
  if (conceptualText.toLowerCase().includes("glossary")) {
    throw new Error("The conceptual question was visibly redirected to the Glossary.");
  }

  // Gate 1 calibration: an ordinary, previously unseen cross-question that
  // should not be accepted as an exact benchmark or deterministic recovery.
  const calibrationQuery = "When a community faces a difficult trade-off between individual freedom and shared responsibility, how should it make a decision that is both fair and workable?";
  await input.fill(calibrationQuery);
  await submit.evaluate(element => setTimeout(() => element.click(), 0));
  const calibrationDeadline = Date.now() + 60_000;
  while (
    !apiResponses.some(item => item.payload && item.payload.query === calibrationQuery) &&
    Date.now() < calibrationDeadline
  ) {
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  await Promise.all(apiBodyReads);
  const calibrationResponses = apiResponses.filter(item =>
    item.payload && item.payload.query === calibrationQuery
  );
  if (!apiRequests.some(request => request.body.query === calibrationQuery)) {
    throw new Error("No real WordPress /api/query request carried the Gate 1 calibration question.");
  }
  const calibrationResponse = calibrationResponses.find(item =>
    item.status === 200 &&
    item.payload?.intent === "TOPICAL_INQUIRY" &&
    typeof item.payload?.response === "string" &&
    item.payload.response.trim().length >= 150 &&
    /freedom/i.test(item.payload.response) &&
    /responsibility/i.test(item.payload.response) &&
    /fair/i.test(item.payload.response)
  );
  if (!calibrationResponse) {
    throw new Error("Gate 1 calibration did not return a substantive, relevant answer. Responses: " +
      JSON.stringify(calibrationResponses.map(item => ({
        status: item.status,
        intent: item.payload?.intent,
        answer_basis: item.payload?.answer_basis,
        response: item.payload?.response,
        recommendation: item.payload?.recommendation
      }))));
  }
  const calibrationRationale = String(
    calibrationResponse.payload?.recommendation?.rationale || ""
  ).replace(/\s+/g, " ").trim();
  if (!calibrationRationale) {
    throw new Error("The community-governance doorway omitted its visitor-facing introduction.");
  }
  if (/^(?:preface|foreword|introduction|abstract|table of contents|contents|chapter\s+\d+|part\s+[ivxlcdm0-9]+)\b/i.test(calibrationRationale) ||
      /meta description|seo description|document type|canonical reference hub/i.test(calibrationRationale) ||
      /the chaos hasn.t fully ended|the losses are still real/i.test(calibrationRationale)) {
    throw new Error("The community-governance doorway exposed source-page prose or internal metadata: " + calibrationRationale);
  }
  const calibrationDoorway = calibrationResponse.payload?.recommendation || {};
  if (
    calibrationDoorway.title !== "The Barangay Before the State: Human-Scale Governance in Practice" ||
    calibrationDoorway.url !== "https://geralddaquila.com/2026/09/21/the-barangay-before-the-state-human-scale-governance-in-practice/" ||
    !/human-scale governance/i.test(calibrationRationale) ||
    !/people affected/i.test(calibrationRationale)
  ) {
    throw new Error("The community-governance doorway did not preserve its verified destination and visitor-facing rationale: " +
      JSON.stringify({title: calibrationDoorway.title, url: calibrationDoorway.url, rationale: calibrationRationale}));
  }
  await page.waitForFunction(() => {
    const root = document.querySelector(".archive-stage-wrapper[data-guide-instance='woody']");
    const text = (root?.querySelector("#archive-response-text")?.innerText || "").toLowerCase();
    return /freedom/.test(text) && /responsibility/.test(text) && /fair/.test(text);
  }, null, { timeout: 60_000 });
  const calibrationUI = (await answer.innerText()).replace(/\s+/g, " ").trim();
  const calibrationAPI = calibrationResponse.payload.response.replace(/\s+/g, " ").trim();
  if (!calibrationUI.toLowerCase().includes("freedom") ||
      !calibrationUI.toLowerCase().includes("responsibility") ||
      !calibrationUI.toLowerCase().includes("fair")) {
    throw new Error("The active Woody instance did not render the Gate 1 calibration answer: " + calibrationUI);
  }
  if (!calibrationUI.toLowerCase().includes(calibrationAPI.slice(0, Math.min(48, calibrationAPI.length)).toLowerCase())) {
    throw new Error("The visible Gate 1 answer did not reflect the API response.");
  }
  console.log(JSON.stringify({
    stage: "gate_1_calibration_response_rendered",
    calibrationQuery,
    calibrationText: calibrationUI,
    answerBasis: calibrationResponse.payload.answer_basis,
    recommendation: calibrationResponse.payload.recommendation || null
  }));
  console.log(JSON.stringify({
    stage: "live_e2e_passed",
    apiOrigin: USE_API_ORIGIN,
    expectedUseVersion: EXPECTED_USE_VERSION || null,
    actualUseVersion: supportedResponse.payload.version,
    conceptualQuery,
    conceptualText,
    rendered,
    rendered,
    elapsedMs: elapsed(),
    apiRequests,
    apiResponses: apiResponses.map(item => ({
      url: item.url,
      status: item.status,
      atMs: item.atMs,
      query: item.payload?.query,
      response: item.payload?.response,
      answer_basis: item.payload?.answer_basis,
      route_source: item.payload?.route_source,
      version: item.payload?.version,
      fingerprint: item.payload?.fingerprint,
      source_sha256: item.payload?.source_sha256,
      recommendation: item.payload?.recommendation,
      bodyReadError: item.bodyReadError
    })),
    apiFailures,
    apiFinished,
    answerLength: responseText.length,
    pageErrors,
    consoleErrors
  }));
} catch (error) {
  console.error(JSON.stringify({
    stage: "live_e2e_failed",
    message: error.message,
    elapsedMs: elapsed(),
    apiRequests,
    apiResponses: apiResponses.map(item => ({
      url: item.url,
      status: item.status,
      atMs: item.atMs,
      recommendation: item.payload?.recommendation,
      bodyReadError: item.bodyReadError
    })),
    apiFailures,
    apiFinished,
    pageErrors,
    controllerSyntaxDiagnostics,
    inlineScriptSyntaxDiagnostics,
    externalScriptSyntaxDiagnostics,
    consoleErrors
  }));
  process.exitCode = 1;
} finally {
  await browser.close();
}
