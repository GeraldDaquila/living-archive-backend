import fs from "node:fs";
import { chromium } from "playwright";

const GUIDE_URL = "https://geralddaquila.com/the-guide-find-your-way2/";
const QUERY = "What is the boiling point of water at sea level?";
const ARTIFACT_DIR = "artifacts";
fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const report = {
  test: "Live WordPress Guide browser E2E — general-knowledge answer",
  guideUrl: GUIDE_URL,
  query: QUERY,
  startedAt: new Date().toISOString(),
  pageStatus: null,
  pageTitle: null,
  pageUrlAfterSubmit: null,
  wrapperCount: null,
  formCount: null,
  queryInputCount: null,
  duplicateIdsWithinGuide: null,
  controllerLoaded: null,
  controllerScriptResponses: [],
  apiRequests: [],
  apiResponses: [],
  pageErrors: [],
  consoleErrors: [],
  failedRequests: [],
  answerText: "",
  recommendationText: "",
  result: "RUNNING",
  failure: null
};

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1365, height: 1000 } });
page.setDefaultTimeout(15_000);
page.setDefaultNavigationTimeout(45_000);

page.on("pageerror", error => report.pageErrors.push(error.message));
page.on("console", message => {
  if (message.type() === "error") report.consoleErrors.push(message.text().slice(0, 700));
});
page.on("requestfailed", request => {
  report.failedRequests.push({
    url: request.url(),
    method: request.method(),
    error: request.failure()?.errorText || "unknown"
  });
});
page.on("request", request => {
  let url;
  try { url = new URL(request.url()); } catch { return; }
  if (url.pathname === "/api/query" && request.method() === "POST") {
    report.apiRequests.push({
      url: request.url(),
      method: request.method(),
      postData: request.postData() || ""
    });
  }
});
page.on("response", response => {
  const url = response.url();
  if (url.includes("living-archive-guide-v489.246-woody.js")) {
    report.controllerScriptResponses.push({ url, status: response.status() });
  }
  try {
    const parsed = new URL(url);
    if (parsed.pathname === "/api/query" && response.request().method() === "POST") {
      report.apiResponses.push({ url, status: response.status() });
    }
  } catch {}
});

try {
  const pageResponse = await page.goto(GUIDE_URL, { waitUntil: "domcontentloaded" });
  report.pageStatus = pageResponse?.status() ?? null;
  report.pageTitle = await page.title();
  if (!pageResponse || pageResponse.status() !== 200) {
    throw new Error(`Guide page returned HTTP ${report.pageStatus}`);
  }

  const rootSelector = '.archive-stage-wrapper[data-guide-instance="woody"]';
  const root = page.locator(rootSelector);
  await root.waitFor({ state: "visible", timeout: 25_000 });
  await root.locator("#archive-search-form").waitFor({ state: "visible" });
  await root.locator("#archive-query-input").waitFor({ state: "visible" });
  await root.locator("#archive-submit-btn").waitFor({ state: "visible" });

  const initial = await page.evaluate((selector) => {
    const roots = [...document.querySelectorAll(selector)];
    const root = roots[0] || null;
    const ids = root ? [...root.querySelectorAll("[id]")].map(el => el.id) : [];
    return {
      wrapperCount: roots.length,
      formCount: root?.querySelectorAll("#archive-search-form").length ?? 0,
      queryInputCount: root?.querySelectorAll("#archive-query-input").length ?? 0,
      buttonCount: root?.querySelectorAll("#archive-submit-btn").length ?? 0,
      duplicateIdsWithinGuide: ids.filter((id, i) => ids.indexOf(id) !== i),
      controllerLoaded: root?.dataset.useScopedControllerLoaded === "1",
      scriptRefs: [...document.scripts].map(script => script.src).filter(src => src.includes("living-archive-guide-v489.246-woody.js"))
    };
  }, rootSelector);
  Object.assign(report, initial);

  if (report.wrapperCount !== 1) throw new Error(`Expected one Woody Guide wrapper, found ${report.wrapperCount}`);
  if (report.formCount !== 1 || report.queryInputCount !== 1 || initial.buttonCount !== 1) {
    throw new Error("The visible Guide form/input/Search button structure is incomplete or duplicated");
  }
  if (report.duplicateIdsWithinGuide.length) {
    throw new Error("Duplicate IDs detected inside the Woody Guide wrapper: " + report.duplicateIdsWithinGuide.join(", "));
  }
  if (!initial.scriptRefs.length) throw new Error("The Woody controller script reference is missing from the rendered page");

  const responseText = root.locator("#archive-response-text");
  const answerBefore = await responseText.innerText().catch(() => "");
  await root.locator("#archive-query-input").fill(QUERY);
  await root.locator("#archive-submit-btn").click();

  await page.waitForFunction(({ selector, previous }) => {
    const root = document.querySelector(selector);
    const text = root?.querySelector("#archive-response-text")?.innerText?.trim() || "";
    const box = root?.querySelector("#archive-response-box");
    const stillLoading = /^(giving this question a little more room|searching|thinking|working on it)[.\\s…]*$/i.test(text);
    // The UI first renders a short progress sentence. Do not treat that transient
    // placeholder as a completed answer: wait for substantive visitor-facing text.
    return text.length > 80 && text !== previous.trim() && !stillLoading &&
      box && getComputedStyle(box).display !== "none";
  }, { selector: rootSelector, previous: answerBefore }, { timeout: 155_000 });

  await page.waitForTimeout(700);
  const rendered = await page.evaluate((selector) => {
    const root = document.querySelector(selector);
    const answer = root?.querySelector("#archive-response-text")?.innerText?.trim() || "";
    const box = root?.querySelector("#archive-response-box");
    const recommendation = root?.querySelector("#archive-recommendation");
    return {
      answerText: answer,
      responseBoxDisplay: box ? getComputedStyle(box).display : null,
      recommendationText: recommendation?.innerText?.trim() || "",
      recommendationDisplay: recommendation ? getComputedStyle(recommendation).display : null,
      url: location.href
    };
  }, rootSelector);
  report.answerText = rendered.answerText;
  report.recommendationText = rendered.recommendationText;
  report.pageUrlAfterSubmit = rendered.url;
  report.responseBoxDisplay = rendered.responseBoxDisplay;
  report.recommendationDisplay = rendered.recommendationDisplay;

  if (report.pageUrlAfterSubmit.split("#")[0] !== GUIDE_URL) {
    throw new Error("The general-knowledge query unexpectedly navigated away from The Guide");
  }
  if (!/100\s*°?C/i.test(report.answerText)) throw new Error("Rendered answer omitted 100°C");
  if (!/212\s*°?F/i.test(report.answerText)) throw new Error("Rendered answer omitted 212°F");
  if (!/standard atmospheric pressure/i.test(report.answerText)) throw new Error("Rendered answer omitted the pressure qualification");
  if (/i haven.t found enough support|rather than fill the gap with outside knowledge/i.test(report.answerText)) {
    throw new Error("Rendered answer retained the Archive-only refusal");
  }
  if (report.apiRequests.length < 1) throw new Error("Browser did not issue a POST to the live /api/query endpoint");
  if (!report.apiRequests.some(item => {
    try {
      const data = JSON.parse(item.postData);
      return data.query === QUERY;
    } catch { return false; }
  })) throw new Error("Captured browser POST did not contain the expected visitor query");
  if (!report.apiResponses.some(item => item.status >= 200 && item.status < 300)) {
    throw new Error("No successful live /api/query response was observed by the browser");
  }
  if (report.pageErrors.length) throw new Error("Browser JavaScript errors: " + report.pageErrors.join(" | "));

  report.result = "PASS";
  report.finishedAt = new Date().toISOString();
  await page.screenshot({ path: `${ARTIFACT_DIR}/live-guide-water-browser-e2e.png`, fullPage: true });
  console.log("LIVE_GUIDE_BROWSER_E2E_RESULT " + JSON.stringify(report));
} catch (error) {
  report.result = "FAIL";
  report.failure = error?.stack || error?.message || String(error);
  report.finishedAt = new Date().toISOString();
  try {
    const current = await page.evaluate((selector) => {
      const root = document.querySelector(selector);
      const button = root?.querySelector("#archive-submit-btn");
      const box = root?.querySelector("#archive-response-box");
      return {
        answerText: root?.querySelector("#archive-response-text")?.innerText?.trim() || "",
        responseBoxDisplay: box ? getComputedStyle(box).display : null,
        buttonDisabled: button?.disabled ?? null,
        buttonLoading: button?.classList.contains("is-loading") ?? null,
        url: location.href
      };
    }, '.archive-stage-wrapper[data-guide-instance="woody"]');
    report.currentDom = current;
    if (!report.answerText) report.answerText = current.answerText;
    if (!report.pageUrlAfterSubmit) report.pageUrlAfterSubmit = current.url;
  } catch (domError) {
    report.domInspectionError = domError.message;
  }
  try {
    await page.screenshot({ path: `${ARTIFACT_DIR}/live-guide-water-browser-e2e.png`, fullPage: true, timeout: 10_000 });
  } catch (screenshotError) {
    report.screenshotError = screenshotError.message;
  }
  console.error("LIVE_GUIDE_BROWSER_E2E_RESULT " + JSON.stringify(report));
  process.exitCode = 1;
} finally {
  fs.writeFileSync(`${ARTIFACT_DIR}/live-guide-water-browser-e2e.json`, JSON.stringify(report, null, 2));
  await browser.close().catch(() => {});
}
