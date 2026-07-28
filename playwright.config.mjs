import { defineConfig, devices } from "@playwright/test";

const port = Number.parseInt(process.env.WEB_TEST_PORT || "4173", 10);
const basePath = process.env.WEB_TEST_BASE_PATH || "/Cheatsheets/";
const siteDir = process.env.SITE_DIR || "site";

export default defineConfig({
  testDir: "./tests/web",
  outputDir: "build/reports/web-test-results",
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  timeout: 30_000,
  expect: {
    timeout: 7_500,
  },
  reporter: [
    ["line"],
    ["json", { outputFile: "build/reports/playwright.json" }],
    ["junit", { outputFile: "build/reports/playwright.xml" }],
  ],
  use: {
    baseURL: `http://127.0.0.1:${port}${basePath}`,
    viewport: { width: 1280, height: 900 },
    actionTimeout: 10_000,
    navigationTimeout: 15_000,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  webServer: {
    command: `python scripts/serve_site.py --site-dir "${siteDir}" --base-path "${basePath}" --port ${port}`,
    url: `http://127.0.0.1:${port}${basePath}`,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
