const { chromium } = require("playwright");
const vm = require("node:vm");

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    await page.addInitScript(() => {
      window.addEventListener("error", (event) => {
        console.log("WINDOW_ERROR " + JSON.stringify({
          message: event.message,
          filename: event.filename,
          line: event.lineno,
          column: event.colno,
          target: event.target && event.target.tagName,
          targetSrc: event.target && event.target.src,
        }));
      }, true);
      window.addEventListener("unhandledrejection", (event) => {
        console.log("WINDOW_UNHANDLED_REJECTION " + String(event.reason));
      });
    });
    page.on("console", (message) => {
      if (
        message.type() === "error" ||
        message.text().startsWith("WINDOW_ERROR ") ||
        message.text().startsWith("WINDOW_UNHANDLED_REJECTION ")
      ) {
        console.log("BROWSER_CONSOLE_EVENT " + JSON.stringify({
          type: message.type(),
          text: message.text(),
          location: message.location(),
        }));
      }
    });
    page.on("pageerror", (error) => {
      console.log("BROWSER_PAGE_ERROR " + JSON.stringify({
        message: error.message,
        stack: error.stack,
      }));
    });

    const navigationResponse = await page.goto("https://geralddaquila.com/the-guide/", {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    if (navigationResponse) {
      const responseHtml = await navigationResponse.text();
      console.log("LIVE_HTML_EXTERNAL_SCRIPT " + JSON.stringify({
        externalAssetReferenced: responseHtml.includes("living-archive-guide-v489.12.js"),
        inlineControllerInHtml: responseHtml.includes("function installGuideSubmitController("),
        inlineEntityEscapedOperators: responseHtml.includes("error &#038;&#038; error.name")
      }));
    }
    const form = page.locator("#archive-search-form");
    await form.waitFor({ state: "attached", timeout: 30000 });
    const state = await form.evaluate((element) => ({
      buildAttribute: element.getAttribute("data-use-frontend-build"),
      installedController: element.__useGuideControllerInstalled || null,
      globalController: window.__USE_GUIDE_FRONTEND_CONTROLLER__ || null,
      externalAssetLoaded: Array.from(document.scripts).some((script) => script.src.includes("living-archive-guide-v489.12.js")),
      formOuterHTML: element.outerHTML.slice(0, 700),
      scripts: Array.from(document.scripts).map((script) => ({
        src: script.src || "",
        length: script.textContent.length,
        firstLine: script.textContent.slice(0, 100).replace(/\n/g, "\\n"),
        build: (script.textContent.match(/var USE_FRONTEND_BUILD = '([^']+)'/) || [])[1] || null,
        hasBrokenEscape: script.textContent.includes(".replace(/'/g, ''');"),
        hasCorrectEscape: script.textContent.includes(".replace(/'/g, '&#39;');"),
      })),
    }));
    console.log("GUIDE_RUNTIME_STATE " + JSON.stringify(state));
    const dataScripts = await page.evaluate(() =>
      Array.from(document.scripts)
        .filter((script) => script.src.startsWith("data:text/javascript;base64,"))
        .map((script) => ({ src: script.src, id: script.id || "" }))
    );
    for (const [index, item] of dataScripts.entries()) {
      const source = Buffer.from(item.src.split(",")[1], "base64").toString("utf8");
      const build = (source.match(/var USE_FRONTEND_BUILD = '([^']+)'/) || [])[1] || null;
      try {
        new vm.Script(source, { filename: "live-data-script-" + (index + 1) });
        console.log("LIVE_DATA_SCRIPT_SYNTAX " + JSON.stringify({index: index + 1, build, length: source.length, syntax: "PASS"}));
      } catch (error) {
        const line = Number((/:(\\d+)$/.exec(error.stack || "") || [])[1] || 0);
        const lines = source.split("\n");
        console.log("LIVE_DATA_SCRIPT_SYNTAX " + JSON.stringify({
          index: index + 1, build, length: source.length, syntax: "FAIL",
          message: error.message, line,
          context: line ? lines.slice(Math.max(0, line - 3), line + 2).map((text, offset) => ({line: Math.max(1, line - 2) + offset, text})) : source.slice(0, 500)
        }));
      }
    }
  } catch (error) {
    console.error("GUIDE_RUNTIME_DIAGNOSTIC_FAIL " + (error.stack || error));
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();
