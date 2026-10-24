import fs from "node:fs";
import { chromium } from "playwright";

const GUIDE_URL = "https://geralddaquila.com/the-guide-find-your-way2/";
const CATALOGUE_PATH = "/explore-the-stewardship-catalogue/";
const ARTIFACT_DIR = "artifacts";
fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const cases = [
  {
    id: "explicit-no-navigation",
    query: "Explain stewardship, but do not send me to another page yet.",
    expected: "answer-first-no-navigation"
  },
  {
    id: "catalogue-resource-discovery",
    query: "Where can I find material about institutional responsibility?",
    expected: "native-catalogue-handoff"
  },
  {
    id: "explicit-glossary-definition",
    query: "What is the canonical Glossary definition of stewardship?",
    expected: "native-glossary-handoff",
    path: "/glossary/"
  },
  {
    id: "explicit-atlas-map",
    query: "Show me the Living Archive Atlas map for stewardship.",
    expected: "native-atlas-handoff",
    path: "/the-living-archive-atlas/"
  },
  {
    id: "explicit-glyph-search",
    query: "Find the Guardian Glyph associated with stewardship.",
    expected: "native-glyph-handoff",
    path: "/guardian-glyph-archives/"
  }
];

const report = {
  test: "Live WordPress Guide browser E2E — routing boundaries",
  guideUrl: GUIDE_URL,
  startedAt: new Date().toISOString(),
  pageErrors: [],
  failedRequests: [],
  cases: [],
  result: "RUNNING",
  failure: null
};

const browser = await chromium.launch({ headless: true });
const rootSelector = '.archive-stage-wrapper[data-guide-instance="woody"]';

async function openGuide(page) {
  const response = await page.goto(GUIDE_URL, { waitUntil: "domcontentloaded" });
  if (!response || response.status() !== 200) {
    throw new Error("Guide returned non-200 status: " + (response?.status() ?? "no response"));
  }
  const root = page.locator(rootSelector);
  await root.waitFor({ state: "visible", timeout: 25_000 });
  await root.locator("#archive-query-input").waitFor({ state: "visible" });
  await root.locator("#archive-submit-btn").waitFor({ state: "visible" });
  return root;
}

try {
  for (const testCase of cases) {
    const page = await browser.newPage({ viewport: { width: 1365, height: 1000 } });
    page.setDefaultTimeout(15_000);
    page.setDefaultNavigationTimeout(45_000);

    const item = {
      id: testCase.id,
      query: testCase.query,
      expected: testCase.expected,
      startUrl: GUIDE_URL,
      apiRequests: [],
      apiResponses: [],
      catalogueRequests: [],
      catalogueResponses: [],
      finalUrl: null,
      destinationUrls: [],
      answerText: "",
      result: "RUNNING",
      failure: null
    };
    page.on("framenavigated", frame => {
      if (frame === page.mainFrame()) {
        try {
          const navigatedUrl = new URL(frame.url());
          if (testCase.path && navigatedUrl.pathname === testCase.path) {
            item.destinationUrls.push(frame.url());
          }
        } catch {}
      }
    });
    page.on("pageerror", error => report.pageErrors.push({ case: testCase.id, error: error.message }));
    page.on("requestfailed", request => report.failedRequests.push({
      case: testCase.id, url: request.url(), error: request.failure()?.errorText || "unknown"
    }));
    page.on("request", request => {
      try {
        const url = new URL(request.url());
        if (url.pathname === "/api/query" && request.method() === "POST") {
          item.apiRequests.push({ url: request.url(), body: request.postData() || "" });
        }
        if (/\/wp-json\/mini-use\/v1\/navigate\/?$/.test(url.pathname) && request.method() === "POST") {
          item.catalogueRequests.push({ url: request.url(), body: request.postData() || "" });
        }
      } catch {}
    });
    page.on("response", response => {
      try {
        const url = new URL(response.url());
        if (url.pathname === "/api/query" && response.request().method() === "POST") {
          item.apiResponses.push({ url: response.url(), status: response.status() });
        }
        if (/\/wp-json\/mini-use\/v1\/navigate\/?$/.test(url.pathname) && response.request().method() === "POST") {
          item.catalogueResponses.push({ url: response.url(), status: response.status() });
        }
      } catch {}
    });

    try {
      const root = await openGuide(page);
      await root.locator("#archive-query-input").fill(testCase.query);
      await root.locator("#archive-submit-btn").click();

      if (testCase.expected === "answer-first-no-navigation") {
        await page.waitForFunction(({ selector }) => {
          const root = document.querySelector(selector);
          const text = root?.querySelector("#archive-response-text")?.innerText?.trim() || "";
          const loading = /^(giving this question a little more room|searching|thinking|working on it)[.\s…]*$/i.test(text);
          return text.length >= 300 && !loading;
        }, { selector: rootSelector }, { timeout: 155_000 });

        item.answerText = await root.locator("#archive-response-text").innerText();
        item.finalUrl = page.url();
        if (new URL(item.finalUrl).origin !== new URL(GUIDE_URL).origin ||
            new URL(item.finalUrl).pathname !== new URL(GUIDE_URL).pathname) {
          throw new Error("Explicit no-navigation request left The Guide: " + item.finalUrl);
        }
        if (!/^stewardship means/i.test(item.answerText.trim())) {
          throw new Error("Stewardship explanation was not answered directly");
        }
        if (/provider bank|canonical evidence|retrieval layer|synthesis layer|processing layer|\bUSE\b/i.test(item.answerText)) {
          throw new Error("Internal implementation jargon leaked into the visitor-facing answer");
        }
        if (/https?:\/\/|\[[^\]]+\]\(/i.test(item.answerText)) {
          throw new Error("The answer embedded a navigation link despite the visitor's explicit instruction");
        }
        if (!item.apiRequests.some(req => {
          try { return JSON.parse(req.body).query === testCase.query; } catch { return false; }
        })) throw new Error("Live API request did not preserve the exact no-navigation question");
        if (!item.apiResponses.some(res => res.status >= 200 && res.status < 300)) {
          throw new Error("No successful API response was observed for no-navigation case");
        }
      } else if (testCase.expected === "native-glossary-handoff" ||
                 testCase.expected === "native-atlas-handoff" ||
                 testCase.expected === "native-glyph-handoff") {
        // These are destination-boundary checks. The Guide must honor an
        // explicit request for a native tool and preserve the original query
        // at the request boundary. Destination-specific search completion
        // remains a separate acceptance check.
        await page.waitForURL(url => url.pathname === testCase.path, { timeout: 45_000 });
        item.finalUrl = page.url();
        const destinationUrlWithQuery = item.destinationUrls
          .map(value => new URL(value))
          .find(url => url.search);
        if (!destinationUrlWithQuery) {
          throw new Error("Native destination navigation never received a query/term parameter");
        }
        if (!item.apiRequests.some(req => {
          try { return JSON.parse(req.body).query === testCase.query; } catch { return false; }
        })) throw new Error("Live Guide API request did not preserve the exact native-destination question");
        if (!item.apiResponses.some(res => res.status >= 200 && res.status < 300)) {
          throw new Error("No successful Guide API response was observed for native-destination case");
        }

        // Assert that each receiving tool actually consumes the handoff and
        // renders a result, not merely that the browser arrived at its URL.
        if (testCase.expected === "native-glossary-handoff") {
          const result = page.locator(".living-glossary-intelligence .lagi-result");
          await result.waitFor({ state: "visible", timeout: 25_000 });
          const canonicalTerm = (await result.locator(".lagi-term-heading").first().innerText()).trim();
          if (canonicalTerm.toLowerCase() !== "stewardship") {
            throw new Error("Glossary rendered the wrong canonical heading: " + canonicalTerm);
          }
          item.answerText = await result.innerText();
          item.destinationResult = { selector: ".living-glossary-intelligence .lagi-result", canonicalTerm };
        } else if (testCase.expected === "native-atlas-handoff") {
          const result = page.locator(".laaf-result");
          await result.waitFor({ state: "visible", timeout: 35_000 });
          const resultText = (await result.innerText()).trim();
          if (resultText.length < 30 || !/atlas map/i.test(resultText)) {
            throw new Error("Atlas Finder did not render a substantive Atlas Map result: " + resultText.slice(0, 300));
          }
          item.answerText = resultText;
          item.destinationResult = { selector: ".laaf-result", textLength: resultText.length };
        } else if (testCase.expected === "native-glyph-handoff") {
          const result = page.locator(".la-glyph-result");
          await result.waitFor({ state: "visible", timeout: 25_000 });
          const resultText = (await result.innerText()).trim();
          if (resultText.length < 30) {
            throw new Error("Glyph Finder result rendered without substantive content");
          }
          item.answerText = resultText;
          item.destinationResult = { selector: ".la-glyph-result", textLength: resultText.length };
        }
      } else {
        await page.waitForURL(url => url.pathname === CATALOGUE_PATH, { timeout: 45_000 });
        item.finalUrl = page.url();

        // Mini-USE intentionally removes catalogue_query from the address bar
        // after reading it, then seeds and submits its own native search form.
        // Validate downstream intake rather than requiring the temporary
        // handoff parameter to remain in the final URL.
        const catalogueInput = page.locator(".mini-use-plugin .mini-use-query").first();
        await catalogueInput.waitFor({ state: "visible", timeout: 20_000 });
        await page.waitForFunction(({ selector, expected }) => {
          const input = document.querySelector(selector);
          return !!input && input.value.trim() === expected;
        }, { selector: ".mini-use-plugin .mini-use-query", expected: testCase.query }, { timeout: 20_000 });

        if (!item.apiRequests.some(req => {
          try { return JSON.parse(req.body).query === testCase.query; } catch { return false; }
        })) throw new Error("Live Guide API request did not preserve the exact Catalogue discovery question");
        if (!item.apiResponses.some(res => res.status >= 200 && res.status < 300)) {
          throw new Error("No successful Guide API response was observed for Catalogue discovery case");
        }
        await page.locator(".mini-use-plugin .mini-use-results:not([hidden])").waitFor({
          state: "visible",
          timeout: 30_000
        }).catch(() => {
          throw new Error("Catalogue did not complete the automatic Mini-USE search for the handed-off question");
        });
        if (!item.catalogueRequests.some(req => {
          try { return JSON.parse(req.body).query === testCase.query; } catch { return false; }
        })) throw new Error("Mini-USE request did not preserve the exact handed-off visitor question");
        if (!item.catalogueResponses.some(res => res.status >= 200 && res.status < 300)) {
          throw new Error("Mini-USE did not return a successful response for the handed-off question");
        }
        item.answerText = "";
      }

      if (report.pageErrors.some(entry => entry.case === testCase.id)) {
        throw new Error("Browser JavaScript error: " + report.pageErrors.filter(entry => entry.case === testCase.id).map(entry => entry.error).join(" | "));
      }
      item.result = "PASS";
    } catch (error) {
      item.result = "FAIL";
      item.failure = error?.stack || error?.message || String(error);
      item.finalUrl = item.finalUrl || page.url();
      try {
        item.answerText = await page.locator(rootSelector + " #archive-response-text").innerText({ timeout: 3000 });
      } catch {}
      report.cases.push(item);
      await page.screenshot({ path: `${ARTIFACT_DIR}/live-guide-routing-${testCase.id}.png`, fullPage: true }).catch(() => {});
      throw error;
    }

    report.cases.push(item);
    await page.screenshot({ path: `${ARTIFACT_DIR}/live-guide-routing-${testCase.id}.png`, fullPage: true }).catch(() => {});
    await page.close();
  }

  if (report.pageErrors.length) throw new Error("One or more browser page errors were observed");
  report.result = "PASS";
  report.finishedAt = new Date().toISOString();
  console.log("LIVE_GUIDE_ROUTING_BROWSER_E2E_RESULT " + JSON.stringify(report));
} catch (error) {
  report.result = "FAIL";
  report.failure = error?.stack || error?.message || String(error);
  report.finishedAt = new Date().toISOString();
  console.error("LIVE_GUIDE_ROUTING_BROWSER_E2E_RESULT " + JSON.stringify(report));
  process.exitCode = 1;
} finally {
  fs.writeFileSync(`${ARTIFACT_DIR}/live-guide-routing-browser-e2e.json`, JSON.stringify(report, null, 2));
  await browser.close().catch(() => {});
}
