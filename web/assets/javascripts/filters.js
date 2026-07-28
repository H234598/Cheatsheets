(() => {
  "use strict";

  const PAGE_BATCH = 24;

  function baseUrl() {
    const meta = document.querySelector('meta[name="cheatsheets-base-url"]');
    try {
      return new URL(meta?.content || "./", document.baseURI);
    } catch {
      return new URL("./", document.baseURI);
    }
  }

  async function fetchData(name) {
    const url = new URL(`data/${name}`, baseUrl());
    if (url.origin !== window.location.origin) {
      throw new Error(`Unsicherer Datenursprung: ${url.origin}`);
    }
    const response = await fetch(url, {
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) throw new Error(`${name}: HTTP ${response.status}`);
    return response.json();
  }

  function normalizedText(value) {
    return String(value || "")
      .normalize("NFKC")
      .toLocaleLowerCase("de")
      .trim();
  }

  function safePageUrl(page) {
    if (!page || typeof page.url !== "string") return null;
    try {
      const url = new URL(page.url, baseUrl());
      return url.origin === window.location.origin ? url : null;
    } catch {
      return null;
    }
  }

  function addOptions(select, values, valueKey, labelKey) {
    const fragment = document.createDocumentFragment();
    for (const item of values) {
      const option = document.createElement("option");
      option.value = String(item[valueKey] || "");
      option.textContent = String(item[labelKey] || item[valueKey] || "");
      fragment.append(option);
    }
    select.append(fragment);
  }

  function searchableText(page) {
    return normalizedText(
      [page.title, ...(page.aliases || []), ...(page.tags || []), page.category_title]
        .filter(Boolean)
        .join(" "),
    );
  }

  function createResult(page) {
    const url = safePageUrl(page);
    if (!url) return null;

    const link = document.createElement("a");
    link.className = "cheat-filter-result";
    link.href = url.href;

    const title = document.createElement("strong");
    title.textContent = page.title || "Unbenanntes Cheatsheet";
    link.append(title);

    const metadata = document.createElement("span");
    const parts = [
      page.category_title,
      Number.isFinite(page.minutes) ? `ca. ${page.minutes} Min.` : null,
    ].filter(Boolean);
    metadata.textContent = parts.join(" · ");
    link.append(metadata);

    if (Array.isArray(page.tags) && page.tags.length) {
      const tags = document.createElement("small");
      tags.textContent = page.tags.slice(0, 5).map((tag) => `#${tag}`).join(" ");
      link.append(tags);
    }
    return link;
  }

  async function initializePanel(panel) {
    const form = panel.querySelector("[data-cheat-filter-form]");
    const queryInput = panel.querySelector("[data-cheat-filter-query]");
    const categorySelect = panel.querySelector("[data-cheat-filter-category]");
    const tagSelect = panel.querySelector("[data-cheat-filter-tag]");
    const timeSelect = panel.querySelector("[data-cheat-filter-time]");
    const results = panel.querySelector("[data-cheat-filter-results]");
    const count = panel.querySelector("[data-cheat-filter-count]");
    const more = panel.querySelector("[data-cheat-filter-more]");
    const error = panel.querySelector("[data-cheat-filter-error]");
    if (!form || !queryInput || !categorySelect || !tagSelect || !timeSelect || !results) {
      return;
    }

    try {
      const [pagePayload, categoryPayload, tagPayload] = await Promise.all([
        fetchData("pages.json"),
        fetchData("categories.json"),
        fetchData("tags.json"),
      ]);
      const pages = Array.isArray(pagePayload) ? pagePayload : [];
      const categories = Array.isArray(categoryPayload) ? categoryPayload : [];
      const tags = Array.isArray(tagPayload) ? tagPayload : [];
      const searchable = new Map(pages.map((page) => [page.id, searchableText(page)]));
      const pagesForTag = new Map(
        tags.map((tag) => [
          String(tag.id || ""),
          new Set(Array.isArray(tag.pages) ? tag.pages : []),
        ]),
      );
      let visibleLimit = PAGE_BATCH;
      let scheduled = false;
      let lastMatches = [];

      addOptions(categorySelect, categories, "id", "title");
      addOptions(tagSelect, tags, "id", "name");

      function matchesFilters(page) {
        const query = normalizedText(queryInput.value);
        if (query && !searchable.get(page.id)?.includes(query)) return false;
        if (categorySelect.value && page.category !== categorySelect.value) return false;
        if (tagSelect.value && !pagesForTag.get(tagSelect.value)?.has(page.id)) {
          return false;
        }
        if (timeSelect.value) {
          const maximumMinutes = Number(timeSelect.value);
          if (!Number.isFinite(maximumMinutes) || Number(page.minutes) > maximumMinutes) {
            return false;
          }
        }
        return true;
      }

      function render() {
        scheduled = false;
        lastMatches = pages
          .filter(matchesFilters)
          .sort((left, right) =>
            String(left.title || "").localeCompare(String(right.title || ""), "de", {
              sensitivity: "base",
            }),
          );
        results.replaceChildren();
        const fragment = document.createDocumentFragment();
        for (const page of lastMatches.slice(0, visibleLimit)) {
          const item = createResult(page);
          if (item) fragment.append(item);
        }
        if (!fragment.childNodes.length) {
          const empty = document.createElement("p");
          empty.className = "cheat-filter-empty";
          empty.textContent = "Keine Cheatsheets entsprechen diesen Filtern.";
          fragment.append(empty);
        }
        results.append(fragment);
        if (count) {
          const shown = Math.min(visibleLimit, lastMatches.length);
          count.textContent = `${lastMatches.length} Treffer, ${shown} sichtbar`;
        }
        if (more) more.hidden = lastMatches.length <= visibleLimit;
      }

      function scheduleRender() {
        visibleLimit = PAGE_BATCH;
        if (scheduled) return;
        scheduled = true;
        window.requestAnimationFrame(render);
      }

      form.addEventListener("submit", (event) => {
        event.preventDefault();
      });
      form.addEventListener("input", scheduleRender);
      form.addEventListener("change", scheduleRender);
      form.addEventListener("reset", () => {
        window.setTimeout(scheduleRender, 0);
      });
      more?.addEventListener("click", () => {
        visibleLimit += PAGE_BATCH;
        render();
      });

      panel.hidden = false;
      render();
    } catch (exception) {
      console.warn("Cheatsheet-Filter konnten nicht initialisiert werden.", exception);
      panel.hidden = false;
      form.hidden = true;
      results.hidden = true;
      if (count) count.hidden = true;
      if (more) more.hidden = true;
      if (error) {
        error.hidden = false;
        error.textContent =
          "Die lokalen Filterdaten sind nicht verfügbar. Kategorien und Gesamtindex funktionieren weiterhin.";
      }
    }
  }

  function initialize() {
    document.querySelectorAll("[data-cheat-filter-panel]").forEach(initializePanel);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }
})();
