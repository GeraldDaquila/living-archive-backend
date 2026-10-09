const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const htmlPath = "wordpress/the-guide-frontend.html";
const jsPath = "wordpress/the-guide-frontend.js";
const html = fs.readFileSync(htmlPath, "utf8");
const source = fs.readFileSync(jsPath, "utf8");
const build = (source.match(/var USE_FRONTEND_BUILD = '([^']+)'/) || [])[1];

assert.ok(build, "Guide external JavaScript build marker is missing.");
assert.ok(html.includes("living-archive-guide-" + build + ".js"),
  "Guide HTML does not reference the matching external JavaScript asset.");
assert.ok(!html.includes("function installGuideSubmitController("),
  "Guide controller must not be embedded in WordPress page content.");

try {
  new vm.Script(source, { filename: jsPath });
  console.log("Guide external JavaScript syntax: PASS (" + build + ")");
} catch (error) {
  console.error("Guide external JavaScript syntax: FAIL");
  console.error(error.stack || error);
  process.exitCode = 1;
}
