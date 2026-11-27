import { chromium } from "playwright";

const GUIDE_URL = "https://geralddaquila.com/the-guide-find-your-way2/?qa_live=extraordinary-claims-20261128";
const PRIMARY_API_ORIGIN = "https://living-archive-backend.onrender.com";
const MIRROR_API_ORIGIN = "https://living-archive-backend-mirror.onrender.com";
const QUERY = "How should the Guide respond to extraordinary claims?";
const EXPECTED_TITLE = "Levels of Claim";
const EXPECTED_URL = "https://geralddaquila.com/levels-of-claim/";
const ROOT = ".archive-stage-wrapper[data-guide-instance='woody']";

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  serviceWorkers: "block",
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 2,
  isMobile: true,
  hasTouch: true
});
const page = await context.newPage();
page.setDefaultTimeout(60_000);
page.setDefaultNavigationTimeout(30_000);

const mirrorAvailableAfterUtc = "2026-12-01";
const mirrorAvailable = new Date().toISOString().slice(0, 10) >= mirrorAvailableAfterUtc;
const blockedMirrorRequests = [];
if (!mirrorAvailable) {
  await page.route(`${MIRROR_API_ORIGIN}/api/query**`, async route => {
    blockedMirrorRequests.push({ url: route.request().url(), method: route.request().method() });
    await route.abort("blockedbyclient");
  });
}

const apiRequests = [];
const apiResponses = [];
const apiBodyReads = [];
const pageErrors = [];
const consoleErrors = [];
page.on("request", request => {
  if (request.method() !== "POST" || !request.url().includes("/api/query")) return;
  let body = {};
  try { body = JSON.parse(request.postData() || "{}"); } catch {}
  apiRequests.push({ url: request.url(), body });
});
page.on("response", response => {
  if (!response.url().includes("/api/query")) return;
  const item = { url: response.url(), status: response.status(), payload: null, bodyReadError: null };
  apiResponses.push(item);
  apiBodyReads.push(response.json().then(payload => { item.payload = payload; }).catch(error => {
    item.bodyReadError = error?.message || String(error);
  }));
});
page.on("pageerror", error => pageErrors.push({ name: error.name, message: error.message }));
page.on("console", message => {
  if (message.type() === "error") consoleErrors.push(message.text());
});

try {
  console.log(JSON.stringify({ stage: "extraordinary_claims_live_acceptance_start", query: QUERY }));
  await page.goto(GUIDE_URL, { waitUntil: "domcontentloaded" });
  await page.waitForLoadState("load").catch(() => {});
  const root = page.locator(ROOT);
  await root.waitFor({ state: "attached" });
  const input = root.locator("#archive-query-input");
  const submit = root.locator("#archive-submit-btn");
  const answer = root.locator("#archive-response-text");
  await input.waitFor({ state: "visible" });
  await submit.waitFor({ state: "visible" });
  await input.fill(QUERY);
  await submit.evaluate(element => setTimeout(() => element.click(), 0));

  const link = root.locator("a.la-answer-doorway__link");
  let waitError = null;
  try {
    await link.waitFor({ state: "visible", timeout: 60_000 });
  } catch (error) {
    waitError = error.message;
  }
  await Promise.all(apiBodyReads);

  const responses = apiResponses.filter(item => item.payload?.query === QUERY);
  const payload = responses.find(item => item.status === 200)?.payload || null;
  const diagnostics = {
    apiRequests,
    apiResponses: responses.map(item => ({
      status: item.status,
      version: item.payload?.version,
      buildProvenance: item.payload?.build_provenance,
      intent: item.payload?.intent,
      response: item.payload?.response,
      recommendation: item.payload?.recommendation,
      canonicalDoorway: item.payload?.canonical_doorway,
      authoritativeDoorway: item.payload?.authoritative_doorway,
      doorwayTitle: item.payload?.doorway_title,
      doorwayUrl: item.payload?.doorway_url,
      doorwayDecision: item.payload?.doorway_decision,
      doorwaySelectionStatus: item.payload?.doorway_selection_status,
      doorwaySelectionSource: item.payload?.doorway_selection_source,
      doorwayOmissionReason: item.payload?.doorway_omission_reason,
      bodyReadError: item.bodyReadError
    })),
    visibleAnswer: await answer.innerText().catch(() => ""),
    rootText: await root.innerText().catch(() => ""),
    links: await root.locator("a").evaluateAll(nodes => nodes.map(node => ({
      text: (node.innerText || node.textContent || "").trim(),
      href: node.href,
      className: node.className,
      visible: Boolean(node.getClientRects().length)
    }))).catch(() => []),
    blockedMirrorRequests,
    pageErrors,
    consoleErrors,
    waitError
  };

  if (!apiRequests.some(item => item.body.query === QUERY)) {
    throw new Error("The real WordPress visitor UI did not submit the exact extraordinary-claims question. " + JSON.stringify(diagnostics));
  }
  if (!payload) {
    throw new Error("The production API returned no readable 200 response for the extraordinary-claims question. " + JSON.stringify(diagnostics));
  }
  if (payload.recommendation?.title !== EXPECTED_TITLE || payload.recommendation?.url !== EXPECTED_URL) {
    throw new Error("The production API did not preserve the reviewed Levels of Claim destination. " + JSON.stringify(diagnostics));
  }
  if (payload.doorway_decision !== "selected" ||
      payload.doorway_selection_status !== "VERIFIED_RELEVANT_DESTINATION") {
    throw new Error("The backend did not mark the canonical doorway as selected and verified. " + JSON.stringify(diagnostics));
  }
  if (!await link.isVisible()) {
    throw new Error("The API selected Levels of Claim but the real WordPress visitor UI did not render its doorway. " + JSON.stringify(diagnostics));
  }
  const rendered = await link.evaluate(node => ({
    title: (node.innerText || node.textContent || "").trim(),
    href: node.href,
    visible: Boolean(node.getClientRects().length)
  }));
  if (rendered.title !== EXPECTED_TITLE || rendered.href !== EXPECTED_URL || !rendered.visible) {
    throw new Error("The rendered visitor doorway does not match the canonical API selection. " + JSON.stringify({ rendered, diagnostics }));
  }
  const answerText = await answer.innerText();
  if (!answerText.trim() || /https?:\\/\\/|www\\./i.test(answerText)) {
    throw new Error("The answer must remain substantive and must not embed the destination URL. " + JSON.stringify({ answerText, diagnostics }));
  }
  if (await answer.locator("a").count() !== 0) {
    throw new Error("The canonical doorway must remain a separate visitor-facing element, not an inline answer link.");
  }

  await page.screenshot({ path: "artifacts/guide-extraordinary-claims-mobile.png", fullPage: true });
  console.log(JSON.stringify({
    stage: "extraordinary_claims_live_acceptance_passed",
    query: QUERY,
    response: payload.response,
    doorway: rendered,
    doorwaySelectionSource: payload.doorway_selection_source,
    version: payload.version,
    buildProvenance: payload.build_provenance,
    mobileViewport: { width: 390, height: 844, deviceScaleFactor: 2, isMobile: true },
    blockedMirrorRequests,
    pageErrors,
    consoleErrors
  }));
} catch (error) {
  console.error(JSON.stringify({
    stage: "extraordinary_claims_live_acceptance_failed",
    message: error.message,
    apiRequests,
    apiResponses: apiResponses.map(item => ({
      status: item.status,
      payload: item.payload,
      bodyReadError: item.bodyReadError
    })),
    blockedMirrorRequests,
    pageErrors,
    consoleErrors
  }));
  process.exitCode = 1;
} finally {
  await browser.close();
}
