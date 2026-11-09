const assert = require('node:assert/strict');
const path = require('node:path');
const { chromium } = require('playwright');

const html = `<!doctype html>
<html>
<body>
<section class="lah-rn" aria-label="Seeing the Relationship">
  <div class="lah-rn-inner">
    <div class="lah-rn-intro">
      <h2><strong>Seeing the Relationship</strong></h2>
      <p>See the relationship before deciding what it means.</p>
      <p class="lah-rn-handoff-status" hidden aria-live="polite"></p>
    </div>
    <div class="lah-rn-current" aria-live="polite"></div>
    <div class="lah-rn-unit-actions" hidden></div>
    <form class="lah-rn-form">
      <label class="screen-reader-text" for="lah-rn-input">What is happening?</label>
      <textarea id="lah-rn-input" class="lah-rn-input" rows="4" maxlength="5000" required></textarea>
      <div class="lah-rn-actions">
        <button type="submit" class="lah-rn-submit">
          <span class="lah-rn-button-label">Continue</span>
          <span class="lah-rn-spinner" aria-hidden="true"></span>
        </button>
      </div>
    </form>
    <div class="lah-rn-record-tools" hidden>
      <button type="button" class="lah-rn-secondary lah-rn-view-record">View conversation</button>
      <button type="button" class="lah-rn-secondary lah-rn-print">Print conversation</button>
    </div>
    <div class="lah-rn-record" hidden>
      <div class="lah-rn-record-header">
        <h3>Conversation</h3>
        <button type="button" class="lah-rn-record-close">Close</button>
      </div>
      <div class="lah-rn-record-body"></div>
    </div>
  </div>
</section>
</body>
</html>`;

const emergencyEndpoint = 'https://hrn.test/wp-json/living-archive/v1/emergency-resources';
const hrnEndpoint = 'https://hrn.test/wp-json/living-archive/v1/relational-navigation';
const jsPath = path.resolve(__dirname, '../../plugins/human-relational-navigator/assets/relational-navigator.js');

async function makePage(browser, failEmergency) {
  const page = await browser.newPage();
  await page.setContent(html);
  await page.evaluate(({ hrnEndpoint, emergencyEndpoint, failEmergency }) => {
    window.LAHRN = {
      endpoint: hrnEndpoint,
      emergency_endpoint: emergencyEndpoint,
      nonce: 'ci-test-nonce',
      guide_return_endpoint: ''
    };
    window.__eiRequests = [];
    window.__eiFail = failEmergency;
    const originalFetch = window.fetch.bind(window);
    window.fetch = async function(input, init) {
      const url = String(input);
      const body = init && init.body ? JSON.parse(init.body) : {};
      if (url === window.LAHRN.endpoint) {
        window.__eiRequests.push({ kind: 'hrn', body });
        return new Response(JSON.stringify({
          safety_interrupt: true,
          safety: 'acute_contact',
          safety_message: 'Please contact emergency or crisis support now.',
          safety_question: 'What country are you in right now?',
          location_required: true,
          resources: []
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (url === window.LAHRN.emergency_endpoint) {
        window.__eiRequests.push({ kind: 'ei', body });
        await new Promise(resolve => setTimeout(resolve, 150));
        if (window.__eiFail === true) {
          return new Response(JSON.stringify({ message: 'Simulated local resource outage' }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
          });
        }
        if (window.__eiFail === 'unverified') {
          return new Response(JSON.stringify({
            operation: 'resource_location_resolution',
            country: 'Philippines',
            stage: 'acute_contact',
            message: 'Please contact emergency or crisis support now.',
            question: 'Stay with another person while you contact support.',
            resources: [],
            resource_provenance: 'ei_no_verified_fallback',
            resource_status: 'ei_no_verified_resource',
            note: 'I could not confirm a current, verified local emergency number for this location. I will not display an unverified number.'
          }), { status: 200, headers: { 'Content-Type': 'application/json' } });
        }
        return new Response(JSON.stringify({
          operation: 'resource_location_resolution',
          country: 'Philippines',
          stage: 'acute_contact',
          message: 'Please contact emergency or crisis support now.',
          question: 'Stay with another person while you contact support.',
          resources: [{
            group: 'Emergency',
            title: 'Unified 911 Emergency Hotline',
            phone: '911',
            hours: '24/7'
          }],
          resource_provenance: 'ei_verified_only',
          resource_status: 'ei_verified_resources',
          note: 'Use this service for immediate emergency assistance.'
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      return originalFetch(input, init);
    };
  }, { hrnEndpoint, emergencyEndpoint, failEmergency });
  await page.addScriptTag({ path: jsPath });
  return page;
}

async function beginLocationFlow(page) {
  await page.locator('.lah-rn-input').fill('I feel unsafe right now.');
  await page.locator('.lah-rn-submit').click();
  await page.locator('.lah-rn-safety-location').waitFor({ state: 'visible', timeout: 5000 });
  await page.locator('.lah-rn-safety-country').fill('Philippines');
  await page.getByRole('button', { name: 'Show local help' }).click();
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const successPage = await makePage(browser, false);
    await beginLocationFlow(successPage);
    const emergencyLink = successPage.locator('.lah-rn-safety-resource a[href="tel:911"]');
    await emergencyLink.waitFor({ state: 'visible', timeout: 12000 });
    assert.equal(await emergencyLink.textContent(), 'Call 911');
    assert.equal(await successPage.locator('.lah-rn.is-loading').count(), 0, 'success path must clear loading state');
    assert.equal(await successPage.locator('.lah-rn-submit').isEnabled(), true, 'success path must restore the composer control');

    const request = await successPage.evaluate(() => window.__eiRequests.find(item => item.kind === 'ei'));
    assert.ok(request, 'browser must issue the EI location-only request');
    assert.deepEqual(Object.keys(request.body).sort(), [
      'country', 'safety_message', 'safety_question', 'safety_stage'
    ], 'EI request must contain only the approved location and safety context fields');
    assert.equal(request.body.country, 'Philippines');
    assert.equal(request.body.safety_stage, 'acute_contact');
    assert.equal(request.body.message, undefined, 'visitor answer must not be passed to EI');
    assert.equal(request.body.conversation, undefined, 'conversation transcript must not be passed to EI');
    await successPage.close();

    const failurePage = await makePage(browser, true);
    await beginLocationFlow(failurePage);
    await failurePage.getByText('I could not load the local resource list right now.', { exact: false })
      .waitFor({ state: 'visible', timeout: 5000 });
    assert.equal(await failurePage.locator('.lah-rn.is-loading').count(), 0, 'error path must clear loading state');
    assert.equal(await failurePage.locator('.lah-rn-submit').isEnabled(), true, 'error path must restore the composer control');
    await failurePage.close();

    const unverifiedPage = await makePage(browser, 'unverified');
    await beginLocationFlow(unverifiedPage);
    await unverifiedPage.getByText('I could not confirm a current, verified local emergency number', { exact: false })
      .waitFor({ state: 'visible', timeout: 5000 });
    assert.equal(await unverifiedPage.locator('a[href^="tel:"]').count(), 0, 'unverified EI outcome must not render a callable telephone link');
    assert.equal(await unverifiedPage.locator('.lah-rn.is-loading').count(), 0, 'unverified outcome must clear loading state');
    await unverifiedPage.close();

    console.log('PASS: browser safety-location flow renders EI-verified resources, withholds unverified numbers, preserves the location-only EI boundary, and clears loading state on success and failure.');
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(error);
  process.exit(1);
});
