import { test, expect } from "@playwright/test";
import path from "node:path";
import { pathToFileURL } from "node:url";

const offlinePort = Number.parseInt(process.env.OFFLINE_TEST_PORT || "4174", 10);
const offlineBaseUrl = `http://127.0.0.1:${offlinePort}/`;
const offlineSiteDir = path.resolve(process.env.OFFLINE_SITE_DIR || "build/offline-site");

function configuredBaseUrl(testInfo) {
  return String(testInfo.project.use.baseURL);
}

function captureBrowserProblems(page) {
  const errors = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("pageerror", (error) => errors.push(error.message));
  return errors;
}

async function restrictRuntimeToOrigin(page, allowedOrigin) {
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

async function loadGraph(request, baseUrl) {
  const response = await request.get(new URL("data/knowledge-graph.json", baseUrl).href);
  expect(response.ok()).toBeTruthy();
  const graph = await response.json();
  expect(graph.schema_version).toBe(1);
  expect(Array.isArray(graph.nodes)).toBeTruthy();
  expect(Array.isArray(graph.edges)).toBeTruthy();
  return graph;
}

async function waitForGraph(page) {
  await page.waitForFunction(
    () => document.documentElement.dataset.cheatsheetGraph === "ready",
  );
}

test("Online-Wissensgraph ist suchbar, tastaturbedienbar und origin-lokal", async ({
  page,
  request,
}, testInfo) => {
  const baseUrl = configuredBaseUrl(testInfo);
  const graph = await loadGraph(request, baseUrl);
  const pageNode = graph.nodes.find((node) => node.type === "page");
  expect(pageNode).toBeTruthy();
  const problems = captureBrowserProblems(page);
  const external = await restrictRuntimeToOrigin(page, new URL(baseUrl).origin);

  const response = await page.goto(new URL("wissensgraph/", baseUrl).href, {
    waitUntil: "domcontentloaded",
  });
  expect(response?.status()).toBe(200);
  await expect(page.getByRole("heading", { name: "Wissensgraph", level: 1 })).toBeVisible();
  await waitForGraph(page);

  const stage = page.locator("[data-cheat-graph-stage]");
  await expect(stage).toBeVisible();
  await expect(stage.locator(".cheat-graph-node")).toHaveCount(graph.nodes.length);
  await expect(page.locator(".cheat-graph-legend")).toBeVisible();

  const search = page.locator("[data-cheat-graph-search]");
  await search.fill(pageNode.label);
  await expect(stage.locator(".cheat-graph-node.is-match").first()).toBeVisible();

  const matchingNode = stage.locator(".cheat-graph-node.is-match").first();
  await matchingNode.focus();
  await expect(matchingNode).toBeFocused();
  await page.keyboard.press("Enter");
  const details = page.locator("[data-cheat-graph-details]");
  await expect(details).toBeVisible();
  await expect(details).toContainText(pageNode.label);
  const openLink = details.getByRole("link", { name: "Knoten öffnen" });
  await expect(openLink).toBeVisible();
  expect(new URL(await openLink.getAttribute("href"), page.url()).origin).toBe(
    new URL(baseUrl).origin,
  );

  await page.goto(baseUrl);
  await page.waitForFunction(
    () => document.documentElement.dataset.cheatsheetUi === "ready",
  );
  await page.keyboard.press("g");
  await page.keyboard.press("w");
  await expect(page).toHaveURL(new URL("wissensgraph/", baseUrl).href);

  expect(problems).toEqual([]);
  expect(external).toEqual([]);
});

test("Offline-Wissensgraph verwendet relative HTML-Ziele und keine fremden Requests", async ({
  page,
  request,
}) => {
  const graph = await loadGraph(request, offlineBaseUrl);
  const pageNode = graph.nodes.find((node) => node.type === "page");
  expect(pageNode.offline_url).toMatch(/\.html$/);
  expect(pageNode.offline_url).not.toMatch(/^https?:|^\//);
  const problems = captureBrowserProblems(page);
  const external = await restrictRuntimeToOrigin(page, new URL(offlineBaseUrl).origin);

  const response = await page.goto(new URL("wissensgraph/index.html", offlineBaseUrl).href, {
    waitUntil: "domcontentloaded",
  });
  expect(response?.status()).toBe(200);
  await waitForGraph(page);
  await expect(page.locator(".cheat-offline-notice")).toBeVisible();

  const node = page.locator(".cheat-graph-node--page").first();
  await node.focus();
  await page.keyboard.press("Enter");
  const link = page
    .locator("[data-cheat-graph-details]")
    .getByRole("link", { name: "Knoten öffnen" });
  await expect(link).toBeVisible();
  const target = new URL(await link.getAttribute("href"), page.url());
  expect(target.origin).toBe(new URL(offlineBaseUrl).origin);
  expect(target.pathname).toMatch(/\.html$/);

  await page.goto(offlineBaseUrl);
  await page.waitForFunction(
    () => document.documentElement.dataset.cheatsheetUi === "ready",
  );
  await page.keyboard.press("g");
  await page.keyboard.press("w");
  await expect(page).toHaveURL(new URL("wissensgraph/index.html", offlineBaseUrl).href);

  expect(problems).toEqual([]);
  expect(external).toEqual([]);
});

test("Wissensgraph besitzt unter file ohne JavaScript einen lesbaren Fallback", async ({
  browser,
}) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  const problems = captureBrowserProblems(page);
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

  const graphUrl = pathToFileURL(
    path.join(offlineSiteDir, "wissensgraph", "index.html"),
  ).href;
  await page.goto(graphUrl, { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "Wissensgraph", level: 1 })).toBeVisible();
  const fallback = page.locator(".cheat-graph-noscript");
  await expect(fallback).toBeVisible();
  const category = fallback.getByRole("link").first();
  await expect(category).toBeVisible();
  expect(await category.getAttribute("href")).toMatch(/index\.html$/);
  await category.click();
  await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible();

  expect(problems).toEqual([]);
  expect(external).toEqual([]);
  await context.close();
});
