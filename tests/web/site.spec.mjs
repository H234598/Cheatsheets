import { test, expect } from "@playwright/test";
import axeCore from "axe-core";

const STORAGE_KEY = "cheatsheets.ui.v1";

function configuredBaseUrl(testInfo) {
  return String(testInfo.project.use.baseURL);
}

async function loadPages(request, testInfo) {
  const response = await request.get(
    new URL("data/pages.json", configuredBaseUrl(testInfo)).href,
  );
  expect(response.ok()).toBeTruthy();
  const payload = await response.json();
  expect(Array.isArray(payload)).toBeTruthy();
  expect(payload.length).toBeGreaterThan(0);
  return payload;
}

function representativePages(pages) {
  const longest = [...pages].sort(
    (left, right) => Number(right.minutes || 0) - Number(left.minutes || 0),
  )[0];
  const hsm = pages.find((page) => /Thales.*HSM/i.test(String(page.title || "")));
  const shortest = [...pages].sort(
    (left, right) => Number(left.minutes || 0) - Number(right.minutes || 0),
  )[0];
  return { longest: hsm || longest, shortest };
}

function localUrl(pageRecord, testInfo) {
  const base = new URL(configuredBaseUrl(testInfo));
  const generated = new URL(String(pageRecord.url), base);
  expect(generated.origin).toBe(base.origin);
  expect(generated.pathname.startsWith(base.pathname)).toBeTruthy();
  return generated.href;
}

function captureBrowserProblems(page) {
  const errors = [];
  page.on("console", (message) => {
    if (message.type() === "error") {
      const location = message.location();
      errors.push(`${message.text()} @ ${location.url || "unknown source"}`);
    }
  });
  page.on("pageerror", (error) => errors.push(error.message));
  return errors;
}

async function restrictRuntimeToLocalOrigin(page, testInfo) {
  const allowedOrigin = new URL(configuredBaseUrl(testInfo)).origin;
  const externalRequests = [];
  await page.route("**/*", async (route) => {
    const requestUrl = new URL(route.request().url());
    if (
      ["http:", "https:"].includes(requestUrl.protocol) &&
      requestUrl.origin !== allowedOrigin
    ) {
      externalRequests.push(requestUrl.href);
      await route.abort("blockedbyclient");
      return;
    }
    await route.continue();
  });
  return externalRequests;
}

async function waitForUi(page) {
  await page.waitForFunction(
    () => document.documentElement.dataset.cheatsheetUi === "ready",
  );
}

async function assertNoSeriousAxeViolations(page) {
  await page.addScriptTag({ content: axeCore.source });
  const results = await page.evaluate(async () =>
    window.axe.run(document, {
      runOnly: {
        type: "tag",
        values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"],
      },
    }),
  );
  const blocking = results.violations.filter((violation) =>
    ["serious", "critical"].includes(violation.impact),
  );
  const detail = blocking
    .map(
      (violation) =>
        `${violation.id} (${violation.impact}): ${violation.help}\n` +
        violation.nodes.map((node) => `  - ${node.target.join(" ")}`).join("\n"),
    )
    .join("\n");
  expect(blocking, detail).toEqual([]);
}

function secondsFromCssDuration(value) {
  return String(value)
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => {
      if (part.endsWith("ms")) return Number.parseFloat(part) / 1000;
      if (part.endsWith("s")) return Number.parseFloat(part);
      return Number.parseFloat(part) || 0;
    });
}

test("Kernseiten laden ohne Browserfehler oder fremde Laufzeitrequests", async ({
  page,
  request,
}, testInfo) => {
  const pages = await loadPages(request, testInfo);
  const { longest, shortest } = representativePages(pages);
  const browserErrors = captureBrowserProblems(page);
  const externalRequests = await restrictRuntimeToLocalOrigin(page, testInfo);
  const targets = [
    configuredBaseUrl(testInfo),
    new URL("kategorien/", configuredBaseUrl(testInfo)).href,
    new URL("downloads/", configuredBaseUrl(testInfo)).href,
    localUrl(shortest, testInfo),
    localUrl(longest, testInfo),
  ];

  for (const target of targets) {
    const response = await page.goto(target, { waitUntil: "domcontentloaded" });
    expect(response?.status(), target).toBe(200);
    await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible();
  }

  expect(browserErrors).toEqual([]);
  expect(externalRequests).toEqual([]);
});

test("Start- und Fachseite haben keine serious oder critical axe-Befunde", async ({
  page,
  request,
}, testInfo) => {
  const pages = await loadPages(request, testInfo);
  const { longest } = representativePages(pages);

  await page.goto(configuredBaseUrl(testInfo));
  await waitForUi(page);
  await assertNoSeriousAxeViolations(page);

  await page.goto(localUrl(longest, testInfo));
  await waitForUi(page);
  await assertNoSeriousAxeViolations(page);
});

test("No-JavaScript-Fallback bleibt vollständig navigierbar", async ({
  browser,
  request,
}, testInfo) => {
  const pages = await loadPages(request, testInfo);
  const { shortest } = representativePages(pages);
  const context = await browser.newContext({
    javaScriptEnabled: false,
    baseURL: configuredBaseUrl(testInfo),
  });
  const page = await context.newPage();

  const home = await page.goto(configuredBaseUrl(testInfo));
  expect(home?.status()).toBe(200);
  await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible();
  await expect(page.locator(".cheat-noscript-note")).toBeVisible();
  await expect(page.getByRole("link", { name: "Kategorie wählen" })).toBeVisible();

  const reference = await page.goto(localUrl(shortest, testInfo));
  expect(reference?.status()).toBe(200);
  await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible();
  await expect(page.locator("[data-cheatsheet-page-tools]")).toBeHidden();
  await context.close();
});

test("Favorit, Fokusmodus, Tastaturhilfe und Suchkürzel funktionieren", async ({
  page,
  request,
}, testInfo) => {
  const pages = await loadPages(request, testInfo);
  const { shortest } = representativePages(pages);
  await page.goto(localUrl(shortest, testInfo));
  await waitForUi(page);

  const tools = page.locator("[data-cheatsheet-page-tools]");
  await expect(tools).toBeVisible();
  const pageId = await tools.getAttribute("data-page-id");
  expect(pageId).toMatch(/^p_[0-9a-f]{16}$/);

  const favorite = page.locator("[data-cheat-favorite]");
  await expect(favorite).toHaveAttribute("aria-pressed", "false");
  await page.keyboard.press("f");
  await expect(favorite).toHaveAttribute("aria-pressed", "true");

  const stored = await page.evaluate((key) => JSON.parse(localStorage.getItem(key)), STORAGE_KEY);
  expect(stored.favorites).toContain(pageId);

  await page.keyboard.press("?");
  await expect(page.locator("[data-cheat-keyboard-dialog][open]")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.locator("[data-cheat-keyboard-dialog]")).not.toHaveAttribute("open", "");

  const focusButton = page.locator("[data-cheat-focus]").first();
  await focusButton.click();
  await expect(page.locator("html")).toHaveAttribute("data-focus-mode", "true");
  await page.keyboard.press("Escape");
  await expect(page.locator("html")).toHaveAttribute("data-focus-mode", "false");

  await page.keyboard.press("/");
  await expect(page.locator('input.md-search__input').first()).toBeFocused();
});

test("Lokale Filter finden Titel und lassen sich vollständig zurücksetzen", async ({
  page,
  request,
}, testInfo) => {
  const pages = await loadPages(request, testInfo);
  const { longest } = representativePages(pages);
  await page.goto(configuredBaseUrl(testInfo));
  await waitForUi(page);

  const panel = page.locator("[data-cheat-filter-panel]");
  await expect(panel).toBeVisible();
  await expect(panel.locator("[data-cheat-filter-count]")).toContainText(
    `${pages.length} Treffer`,
  );

  await panel.locator("[data-cheat-filter-query]").fill(longest.title);
  await expect(
    panel.locator("[data-cheat-filter-results]").getByText(longest.title, {
      exact: true,
    }),
  ).toBeVisible();

  await panel.getByRole("button", { name: "Filter zurücksetzen" }).click();
  await expect(panel.locator("[data-cheat-filter-count]")).toContainText(
    `${pages.length} Treffer`,
  );
});

test("320-Pixel-Ansicht, Fokus und Reduced Motion bleiben robust", async ({
  page,
  request,
}, testInfo) => {
  const pages = await loadPages(request, testInfo);
  const { longest } = representativePages(pages);
  await page.setViewportSize({ width: 320, height: 800 });
  await page.emulateMedia({ reducedMotion: "reduce", colorScheme: "dark" });
  await page.goto(localUrl(longest, testInfo));
  await waitForUi(page);

  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(1);

  const favorite = page.locator("[data-cheat-favorite]");
  await favorite.focus();
  await expect(favorite).toBeFocused();
  const focusStyle = await favorite.evaluate((element) => {
    const style = getComputedStyle(element);
    return {
      outlineStyle: style.outlineStyle,
      outlineWidth: Number.parseFloat(style.outlineWidth),
      transitionDuration: style.transitionDuration,
      animationDuration: style.animationDuration,
      reduced: matchMedia("(prefers-reduced-motion: reduce)").matches,
    };
  });
  expect(focusStyle.outlineStyle).not.toBe("none");
  expect(focusStyle.outlineWidth).toBeGreaterThanOrEqual(2);
  expect(focusStyle.reduced).toBeTruthy();
  expect(Math.max(...secondsFromCssDuration(focusStyle.transitionDuration))).toBeLessThanOrEqual(
    0.001,
  );
  expect(Math.max(...secondsFromCssDuration(focusStyle.animationDuration))).toBeLessThanOrEqual(
    0.001,
  );

  const codeBlock = page.locator(".md-typeset pre").first();
  await expect(codeBlock).toBeVisible();
  expect(
    await codeBlock.evaluate((element) => getComputedStyle(element).overflowX),
  ).toMatch(/auto|scroll/);

  const tableContainer = page.locator(".md-typeset__table").first();
  if ((await tableContainer.count()) > 0) {
    expect(
      await tableContainer.evaluate((element) => getComputedStyle(element).overflowX),
    ).toMatch(/auto|scroll/);
  }
});

test("Downloadartefakte sind lokal erreichbar und die 404-Seite antwortet korrekt", async ({
  page,
  request,
}, testInfo) => {
  const downloads = await page.goto(
    new URL("downloads/", configuredBaseUrl(testInfo)).href,
  );
  expect(downloads?.status()).toBe(200);
  const artifact = page.locator('a[download][href^="files/"]').first();
  await expect(artifact).toBeVisible();
  const href = await artifact.getAttribute("href");
  const artifactResponse = await request.get(new URL(href, page.url()).href);
  expect(artifactResponse.ok()).toBeTruthy();
  expect((await artifactResponse.body()).byteLength).toBeGreaterThan(0);

  const missing = await page.goto(
    new URL("absichtlich-nicht-vorhanden/", configuredBaseUrl(testInfo)).href,
  );
  expect(missing?.status()).toBe(404);
  await expect(
    page.getByRole("heading", { name: "Seite nicht gefunden", level: 1 }),
  ).toBeVisible();
  const homeLink = page.getByRole("link", { name: "Zur Startseite" });
  await expect(homeLink).toBeVisible();
  const homeHref = await homeLink.getAttribute("href");
  expect(new URL(homeHref, page.url()).href).toBe(configuredBaseUrl(testInfo));
  await homeLink.click();
  await expect(page).toHaveURL(configuredBaseUrl(testInfo));
});
