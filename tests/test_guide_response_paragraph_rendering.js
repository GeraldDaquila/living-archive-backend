const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync(process.argv[2], 'utf8');
const start = source.indexOf('function normalizeGuideEscapedLineBreaks');
const end = source.indexOf('\\nfunction useGuideSubmit', start);
if (start < 0 || end < 0) throw new Error('renderer function not found');
const code = source.slice(start, end) + '\\n' + [
  "function escapeHtml(value) { return String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\\\"/g, '&quot;').replace(/'/g, '&#39;'); }",
  "var marked = { parse: function(value) { return '<marked>' + value + '</marked>'; } };",
  "globalThis.__render = renderGuideAnswer;"
].join('\\n');
const context = {};
vm.createContext(context);
vm.runInContext(code, context);
function assert(condition, message) { if (!condition) throw new Error(message); }
const rendered1 = context.__render("Opening sentence.\\\\n\\\\nSecond paragraph.\\\\n\\\\nFinal paragraph.");
assert((rendered1.match(/<p>/g) || []).length === 3, 'escaped paragraph boundaries not preserved');
const rendered2 = context.__render("Opening sentence.\\n\\nSecond paragraph.");
assert((rendered2.match(/<p>/g) || []).length === 2, 'real paragraph boundaries not preserved');
const rendered3 = context.__render("Opening sentence. Second sentence. A useful place to continue: <a href='https://geralddaquila.com/test'>Test</a>");
assert((rendered3.match(/<p>/g) || []).length === 2, 'single-line long response not split at transition boundary');
assert(!rendered3.includes('<a href='), 'HTML must not be inserted by fallback paragraph formatter');
console.log('PASS: escaped and real paragraph boundaries; transition split; rendering output checked');