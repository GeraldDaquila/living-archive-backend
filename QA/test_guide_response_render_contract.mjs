import fs from "node:fs";
import vm from "node:vm";

const source = fs.readFileSync("wordpress/living-archive-guide-v489.247-response-integrity.js", "utf8");
const start = source.indexOf("function renderGuideAnswer(response)");
const end = source.indexOf("\nfunction useGuideSubmit", start);
if (start < 0 || end < 0) throw new Error("Guide answer renderer boundaries not found");

const context = {
  escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  },
  marked: { parse(value) { return "<marked>" + value + "</marked>"; } }
};
vm.createContext(context);
vm.runInContext(source.slice(start, end) + "\nthis.rendered = renderGuideAnswer;", context);

const renderer = context.rendered;
const paragraphResponse = "First paragraph.\\n\\nSecond paragraph.\\n\\nThird paragraph.";
const escapedResponse = "First paragraph.\\\\n\\\\nSecond paragraph.";
const singleResponse = "A single paragraph remains intact.";

const paragraphHtml = renderer(paragraphResponse);
const escapedHtml = renderer(escapedResponse);
const singleHtml = renderer(singleResponse);

if (paragraphHtml && typeof paragraphHtml.then === "function") throw new Error("renderer must return HTML, not a Promise");
if ((paragraphHtml.match(/<p>/g) || []).length !== 3) throw new Error("real paragraph boundaries were not preserved");
if ((escapedHtml.match(/<p>/g) || []).length !== 2) throw new Error("escaped paragraph boundaries were not preserved");
if (!singleHtml.includes("<marked>")) throw new Error("single paragraph markdown path regressed");

console.log("PASS: Guide renderer is synchronous and preserves paragraph boundaries");
