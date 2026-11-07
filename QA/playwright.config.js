const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: '.',
  timeout: 45000,
  use: {
    baseURL: process.env.GUIDE_URL || 'https://geralddaquila.com/the-guide-find-your-way2/',
    headless: true
  },
  reporter: [['list'], ['html', { outputFolder: 'playwright-report', open: 'never' }]]
});
