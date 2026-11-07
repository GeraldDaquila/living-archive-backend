const { test, expect } = require('@playwright/test');

const GUIDE_URL = process.env.GUIDE_URL || 'https://geralddaquila.com/the-guide-find-your-way2/';
const SHADOW_HOST = process.env.PREDICTIVE_SHADOW_HOST || 'living-archive-predictive-shadow.onrender.com';
const PROD_HOST = process.env.PRODUCTION_HOST || 'living-archive-backend.onrender.com';

async function submitAndCapture(page, url, question) {
  const lifecycle = {
    page: url,
    console: [],
    requests: [],
    responses: [],
    failures: [],
    selectedBackend: null
  };

  page.on('console', msg => lifecycle.console.push({ type: msg.type(), text: msg.text() }));
  page.on('request', request => {
    if (request.url().includes('/api/query')) {
      lifecycle.requests.push({ method: request.method(), url: request.url(), postData: request.postData() });
    }
  });
  page.on('response', response => {
    if (response.url().includes('/api/query')) {
      lifecycle.responses.push({ status: response.status(), url: response.url() });
    }
  });
  page.on('requestfailed', request => {
    if (request.url().includes('/api/query')) {
      lifecycle.failures.push({ url: request.url(), failure: request.failure()?.errorText || 'unknown' });
    }
  });

  await page.goto(url, { waitUntil: 'domcontentloaded' });

  const box = page.locator('textarea').first();
  await expect(box).toBeVisible();
  await box.fill(question);
  await page.getByRole('button', { name: /search/i }).first().click();

  await page.waitForTimeout(5000);
  lifecycle.selectedBackend = await page.evaluate(() => window.__LIVING_ARCHIVE_GUIDE_BACKEND || null);
  return lifecycle;
}

function lifecycleMessage(lifecycle) {
  return JSON.stringify(lifecycle, null, 2);
}

test('production Guide query stays on the production service', async ({ page }) => {
  const result = await submitAndCapture(page, GUIDE_URL, 'What does stewardship mean here?');
  expect(result.requests, lifecycleMessage(result)).not.toHaveLength(0);
  expect(result.requests.some(request => new URL(request.url).host === PROD_HOST), lifecycleMessage(result)).toBeTruthy();
});

test('predictive-shadow controlled query set reaches shadow without production fallback', async ({ page }) => {
  const separator = GUIDE_URL.includes('?') ? '&' : '?';
  const url = GUIDE_URL + separator + 'guide_backend=predictive-shadow';
  const questions = [
    'What does stewardship mean here?',
    'How can I tell whether a system is healthy?',
    'Why does governance become detached from reality?',
    'Where should I begin when I feel disoriented?',
    'How do feedback and correctability relate?'
  ];

  for (const question of questions) {
    const result = await submitAndCapture(page, url, question);
    expect(result.console.some(entry => entry.text.includes('[The Guide] backend mode: predictive-shadow')), lifecycleMessage(result)).toBeTruthy();
    expect(result.requests, lifecycleMessage(result)).not.toHaveLength(0);
    expect(result.requests.some(request => new URL(request.url).host === SHADOW_HOST), lifecycleMessage(result)).toBeTruthy();
    expect(result.requests.some(request => new URL(request.url).host === PROD_HOST), lifecycleMessage(result)).toBeFalsy();
  }
});
