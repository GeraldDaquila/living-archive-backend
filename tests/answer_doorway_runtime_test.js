'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const context = {
  window: { location: { origin: 'https://geralddaquila.com' } },
  document: {}
};
vm.runInNewContext(
  fs.readFileSync('wordpress/living-archive-answer-doorway-standard/assets/answer-doorway.js', 'utf8'),
  context,
  { filename: 'answer-doorway.js' }
);
const doorway = context.window.LivingArchiveAnswerDoorway;

assert.equal(doorway.version, '1.0.0');
assert.equal(doorway.normalizeUrl('https://geralddaquila.com/systems-structure/'), 'https://geralddaquila.com/systems-structure/');
for (const url of [
  '/systems-structure/',
  'http://geralddaquila.com/systems-structure/',
  'https://geralddaquila.com.evil.example/systems-structure/',
  'https://user@geralddaquila.com/systems-structure/',
  'https://geralddaquila.com:8443/systems-structure/',
  'https://geralddaquila.com/systems-structure/?next=https://evil.example/',
  'https://geralddaquila.com/systems-structure/#fragment',
  'javascript:alert(1)'
]) {
  assert.equal(doorway.normalizeUrl(url), null, 'must reject ' + url);
}
assert.ok(doorway.normalize({
  title: 'Systems, Governance, and Organizational Design',
  url: 'https://geralddaquila.com/systems-structure/',
  rationale: 'This hub examines how structures, incentives, governance arrangements, and complexity shape system behavior.'
}));
assert.equal(doorway.normalize({
  title: 'Generic',
  url: 'https://geralddaquila.com/systems-structure/',
  rationale: 'There is something here worth staying with.'
}), null);
assert.equal(doorway.normalize({
  title: 'x'.repeat(181),
  url: 'https://geralddaquila.com/systems-structure/',
  rationale: 'A grounded rationale.'
}), null);
assert.equal(doorway.normalize({
  title: 'Valid',
  url: 'https://geralddaquila.com/systems-structure/',
  rationale: 'x'.repeat(601)
}), null);
process.stdout.write('ANSWER DOORWAY RUNTIME SECURITY TEST: PASS\n');
