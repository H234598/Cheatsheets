import { test, expect } from "@playwright/test";
import path from "node:path";
import { pathToFileURL } from "node:url";

const offlinePort = Number.parseInt(process.env.OFFLINE_TEST_PORT || "4174", 10);
const offlineBaseUrl = `http://127.0.0.1:${offlinePort}/`;
const offlineSiteDir = path.resolve(process.env.OFFLINE_SITE_DIR || "build/offline-site");

function captureProblems(page) {
  const errors = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("pageerror", (error) => errors.push(error.message));
  return errors;
}

async function blockExternalRuntime(page, allowedOrigin) {
  const external = [];
  await page.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (["http:", "https:"].includes(url.protocol) && url.origin !== allowedOrigin) {
      external.push(url.href);
      await route.abort("blockedbyclient");
      return;
    }
    await route.continue();
  });
  return external;
}

async function waitForUi(page) {
  await page.waitForFunction(
    () => document.documentElement.dataset.cheatsheetUi === "ready",
  );
}

test("entpacktes Offlinepaket funktioniert über den lokalen Server vollständig", async ({
  page,
  request,
}) => {
  const problems = captureProblems(page);
  const external = await blockExternalRuntime(page, new URL(offlineBaseUrl).origin);

  const pagesResponse = await request.get(new URL("data/pages.json", offlineBaseUrl).href);
  expect(pagesResponse.ok()).toBeTruthy();
  const pages = await pagesResponse.json();
  expect(Array.isArray(pages)).toBeTruthy();
  expect(pages.length).toBeGreaterThan(0);
  const reference = pages[0];
  expect(reference.url).toMatch(/\.html$/);
  expect(reference.url).not.toMatch(/^https?:|^\//);

  const response = await page.goto(offlineBaseUrl, { waitUntil: "domcontentloaded" });
  expect(response?.status()).toBe(200);
  await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible();
  await expect(page.locator(".cheat-offline-notice")).toBeVisible();
  await waitForUi(page);

  const filter = page.locator("[data-cheat-filter-panel]");
  await expect(filter).toBeVisible();
  await expect(filter.locator("[data-cheat-filter-count]")).toContainText(
    `${pages.length} Treffer`,
  );

  const referenceUrl = new URL(reference.url, offlineBaseUrl).href;
  const referenceResponse = await page.goto(referenceUrl, {
    waitUntil: "domcontentloaded",
  });
  expect(referenceResponse?.status()).toBe(200);
  await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible();
  await expect(page.locator(".cheat-offline-notice")).toBeVisible();
  await waitForUi(page);

  expect(problems).toEqual([]);
  expect(external).toEqual([]);
});

test("file-Fallback bleibt ohne JavaScript lesbar und navigierbar", async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  const problems = captureProblems(page);
  const external = [];
  await page.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (["http:", "https:"].includes(url.protocol)) {
      external.push(url.href);
      await route.abort("blockedbyclient");
      return;
    }
    await route.continue();
  });

  const indexUrl = pathToFileURL(path.join(offlineSiteDir, "index.html")).href;
  await page.goto(indexUrl, { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible();
  await expect(page.locator(".cheat-offline-notice")).toBeVisible();
  await expect(page.locator(".cheat-noscript-note")).toBeVisible();

  const category = page.getByRole("link", { name: "Kategorie wählen" });
  await expect(category).toBeVisible();
  const href = await category.getAttribute("href");
  expect(href).toMatch(/kategorien\.html$/);
  await category.click();
  await expect(page).toHaveURL(/\/kategorien\.html$/);
  await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible();

  expect(problems).toEqual([]);
  expect(external).toEqual([]);
  await context.close();
});
