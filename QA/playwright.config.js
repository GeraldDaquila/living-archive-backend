const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: __dirname,
  testMatch: 'test_guide_browser_routing.js',
  timeout: 45000,
  use: {
    baseURL: process.env.GUIDE_URL || 'https://geralddaquila.com/the-guide-find-your-way2/',
    headless: true,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure'
  },
  reporter: [['list'], ['html', { outputFolder: 'playwright-report', open: 'never' }]]
});
