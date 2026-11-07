const { test, expect } = require('@playwright/test');

const GUIDE_URL = process.env.GUIDE_URL || 'https://geralddaquila.com/the-guide-find-your-way2/';
const SHADOW_HOST = process.env.PREDICTIVE_SHADOW_HOST || 'living-archive-predictive-shadow.onrender.com';
const PROD_HOST = process.env.PRODUCTION_HOST || 'living-archive-backend.onrender.com';

async function submitAndCapture(page, url, question) {
  const requests = [];
  page.on('request', request => {
    if (request.url().includes('/api/query')) requests.push(request.url());
  });
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  const box = page.locator('textarea').first();
  await expect(box).toBeVisible();
  await box.fill(question);
  await Promise.all([
    page.waitForResponse(response => response.url().includes('/api/query'), { timeout: 40000 }),
    page.getByRole('button', { name: /search/i }).first().click()
  ]);
  return requests;
}

test('production Guide query stays on the production service', async ({ page }) => {
  const requests = await submitAndCapture(
    page,
    GUIDE_URL,
    'What does stewardship mean here?'
  );
  expect(requests.some(url => new URL(url).host === PROD_HOST)).toBeTruthy();
});

test('predictive-shadow opt-in reaches the shadow service and never silently falls back', async ({ page }) => {
  const separator = GUIDE_URL.includes('?') ? '&' : '?';
  const url = GUIDE_URL + separator + 'guide_backend=predictive-shadow';
  const requests = await submitAndCapture(
    page,
    url,
    'What does stewardship mean here?'
  );
  expect(requests).not.toHaveLength(0);
  expect(requests.some(request => new URL(request).host === SHADOW_HOST)).toBeTruthy();
  expect(requests.some(request => new URL(request).host === PROD_HOST)).toBeFalsy();
});
