const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./tests",
  timeout: 120000,
  expect: { timeout: 10000 },
  retries: 0,
  use: {
    baseURL: process.env.UAT_BASE_URL || "http://127.0.0.1:8090",
    video: "on",
    screenshot: "on",
    trace: "on",
    viewport: { width: 1280, height: 720 },
  },
});
