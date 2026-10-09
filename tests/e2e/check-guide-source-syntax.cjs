const fs = require("node:fs");
const vm = require("node:vm");

const sourcePath = "wordpress/the-guide-frontend.html";
const html = fs.readFileSync(sourcePath, "utf8");
const scripts = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)]
  .filter((match) => !/\bsrc\s*=/.test(match[1]))
  .map((match, index) => ({ index: index + 1, source: match[2] }));

if (scripts.length === 0) {
  throw new Error("No inline Guide frontend script was found.");
}

for (const script of scripts) {
  try {
    new vm.Script(script.source, { filename: sourcePath + "#inline-script-" + script.index });
    console.log("Inline Guide script " + script.index + ": syntax PASS");
  } catch (error) {
    console.error("Inline Guide script " + script.index + ": syntax FAIL");
    console.error(error.stack || error);
    process.exitCode = 1;
  }
}
