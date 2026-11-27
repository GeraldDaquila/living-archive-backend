import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const prompt = readFileSync("general_guide_composition.py", "utf8");
const css = readFileSync("wordpress/living-archive-answer-doorway-standard/assets/answer-doorway.css", "utf8");
const controller = readFileSync("wordpress/living-archive-answer-doorway-standard/assets/guide-controller-v489.333.js", "utf8");

assert.match(prompt, /VISITOR IDEA-CHUNKING AND READABILITY:/);
assert.match(prompt, /one main idea per short paragraph/);
assert.match(prompt, /Preserve reasoning and qualifications/);
assert.match(css, /#archive-response-text[\s\S]*?font-size: 18px !important/);
assert.match(css, /max-width: 66ch/);
assert.match(css, /line-height: 1\.78 !important/);
assert.match(controller, /USE_FRONTEND_BUILD = 'v489\.333-semantic-answer-presentation'/);
assert.match(controller, /function renderGuideAnswerContent\(/);
assert.equal((controller.match(/renderGuideAnswerContent\(responseText, data\.response\)/g) || []).length, 2,
  "main answers and ordinary follow-ups must share the same renderer");
assert.match(controller, /sanitizeMarkdown\(html\)/);
assert.match(controller, /target\.replaceChildren\(fragment\)/);
console.log("PASS: Guide semantic chunking, shared rendering, and mobile typography contract");
