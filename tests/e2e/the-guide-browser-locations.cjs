const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    page.on("console", (message) => {
      if (message.type() === "error") {
        console.log("BROWSER_CONSOLE_ERROR " + JSON.stringify({
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

    await page.goto("https://geralddaquila.com/the-guide/", {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    const form = page.locator("#archive-search-form");
    await form.waitFor({ state: "attached", timeout: 30000 });
    const state = await form.evaluate((element) => ({
      buildAttribute: element.getAttribute("data-use-frontend-build"),
      installedController: element.__useGuideControllerInstalled || null,
      globalController: window.__USE_GUIDE_FRONTEND_CONTROLLER__ || null,
      scripts: Array.from(document.scripts).map((script) => ({
        src: script.src || "",
        length: script.textContent.length,
        build: (script.textContent.match(/var USE_FRONTEND_BUILD = '([^']+)'/) || [])[1] || null,
        hasBrokenEscape: script.textContent.includes(".replace(/'/g, ''');"),
        hasCorrectEscape: script.textContent.includes(".replace(/'/g, '&#39;');"),
      })),
    }));
    console.log("GUIDE_RUNTIME_STATE " + JSON.stringify(state));
  } catch (error) {
    console.error("GUIDE_RUNTIME_DIAGNOSTIC_FAIL " + (error.stack || error));
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();
