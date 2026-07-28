(() => {
  "use strict";

  const STORAGE_KEY = "cheatsheets.ui.v1";
  const SCHEMA_VERSION = 1;
  const MAX_FAVORITES = 100;
  const MAX_PROGRESS_ENTRIES = 200;
  const GOTO_TIMEOUT_MS = 1500;

  const EMPTY_STATE = Object.freeze({
    schema: SCHEMA_VERSION,
    favorites: [],
    lastRead: null,
    progress: {},
    preferences: {
      focusMode: false,
      shortcuts: true,
    },
  });

  let storageAvailable = true;
  let state = cloneEmptyState();
  let pages = [];
  let pageById = new Map();
  let currentPageId = null;
  let gotoDeadline = 0;
  let progressFrame = null;
  let lastProgressWrite = 0;

  function cloneEmptyState() {
    return {
      schema: SCHEMA_VERSION,
      favorites: [],
      lastRead: null,
      progress: {},
      preferences: {
        focusMode: false,
        shortcuts: true,
      },
    };
  }

  function isPlainObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

  function isPageId(value) {
    return typeof value === "string" && /^p_[0-9a-f]{16}$/.test(value);
  }

  function normalizeTimestamp(value) {
    if (typeof value !== "string") return null;
    const parsed = Date.parse(value);
    return Number.isFinite(parsed) ? new Date(parsed).toISOString() : null;
  }

  function normalizeProgressEntry(value) {
    if (!isPlainObject(value)) return null;
    const ratio = Number(value.ratio);
    const updatedAt = normalizeTimestamp(value.updatedAt);
    if (!Number.isFinite(ratio) || !updatedAt) return null;
    return {
      ratio: Math.min(1, Math.max(0, ratio)),
      section: typeof value.section === "string" ? value.section.slice(0, 200) : null,
      updatedAt,
    };
  }

  function normalizeState(value) {
    const normalized = cloneEmptyState();
    if (!isPlainObject(value) || value.schema !== SCHEMA_VERSION) return normalized;

    if (Array.isArray(value.favorites)) {
      normalized.favorites = [...new Set(value.favorites.filter(isPageId))].slice(
        0,
        MAX_FAVORITES,
      );
    }

    if (isPlainObject(value.lastRead) && isPageId(value.lastRead.pageId)) {
      const updatedAt = normalizeTimestamp(value.lastRead.updatedAt);
      if (updatedAt) {
        normalized.lastRead = {
          pageId: value.lastRead.pageId,
          section:
            typeof value.lastRead.section === "string"
              ? value.lastRead.section.slice(0, 200)
              : null,
          updatedAt,
        };
      }
    }

    if (isPlainObject(value.progress)) {
      const entries = Object.entries(value.progress)
        .filter(([pageId]) => isPageId(pageId))
        .map(([pageId, entry]) => [pageId, normalizeProgressEntry(entry)])
        .filter(([, entry]) => entry !== null)
        .sort((left, right) => Date.parse(right[1].updatedAt) - Date.parse(left[1].updatedAt))
        .slice(0, MAX_PROGRESS_ENTRIES);
      normalized.progress = Object.fromEntries(entries);
    }

    if (isPlainObject(value.preferences)) {
      normalized.preferences.focusMode = value.preferences.focusMode === true;
      normalized.preferences.shortcuts = value.preferences.shortcuts !== false;
    }
    return normalized;
  }

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return normalizeState(raw ? JSON.parse(raw) : null);
    } catch {
      storageAvailable = false;
      return cloneEmptyState();
    }
  }

  function saveState() {
    if (!storageAvailable) return false;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      return true;
    } catch {
      storageAvailable = false;
      updateStorageNotice();
      return false;
    }
  }

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

  function migrateId(pageId, aliases) {
    let current = pageId;
    const seen = new Set();
    while (isPageId(current) && isPageId(aliases[current]) && !seen.has(current)) {
      seen.add(current);
      current = aliases[current];
    }
    return current;
  }

  function migrateState(aliasPayload) {
    const aliases = isPlainObject(aliasPayload?.aliases) ? aliasPayload.aliases : {};
    let changed = false;

    const migratedFavorites = [
      ...new Set(state.favorites.map((pageId) => migrateId(pageId, aliases))),
    ].filter(isPageId);
    if (JSON.stringify(migratedFavorites) !== JSON.stringify(state.favorites)) changed = true;
    state.favorites = migratedFavorites.slice(0, MAX_FAVORITES);

    if (state.lastRead) {
      const migrated = migrateId(state.lastRead.pageId, aliases);
      if (migrated !== state.lastRead.pageId) changed = true;
      state.lastRead.pageId = migrated;
    }

    const migratedProgress = {};
    for (const [pageId, entry] of Object.entries(state.progress)) {
      const migrated = migrateId(pageId, aliases);
      if (migrated !== pageId) changed = true;
      const existing = migratedProgress[migrated];
      if (!existing || Date.parse(entry.updatedAt) > Date.parse(existing.updatedAt)) {
        migratedProgress[migrated] = entry;
      }
    }
    state.progress = migratedProgress;
    if (changed) saveState();
  }

  function pageToolRoot() {
    return document.querySelector("[data-cheatsheet-page-tools]");
  }

  function readCurrentPageId() {
    const value = pageToolRoot()?.dataset.pageId || "";
    return isPageId(value) ? value : null;
  }

  function updateStorageNotice() {
    document.documentElement.dataset.cheatsheetStorage = storageAvailable
      ? "available"
      : "unavailable";
    document.querySelectorAll("[data-cheat-storage-note]").forEach((element) => {
      element.hidden = storageAvailable;
    });
  }

  function updateFavoriteButton() {
    const active = Boolean(currentPageId && state.favorites.includes(currentPageId));
    document.querySelectorAll("[data-cheat-favorite]").forEach((button) => {
      button.setAttribute("aria-pressed", String(active));
      button.dataset.active = String(active);
      const label = active ? "Aus Favoriten entfernen" : "Zu Favoriten hinzufügen";
      button.setAttribute("aria-label", label);
      const text = button.querySelector("[data-cheat-button-label]");
      if (text) text.textContent = active ? "Favorit" : "Merken";
    });
  }

  function toggleFavorite() {
    if (!currentPageId) return;
    const favorites = new Set(state.favorites);
    if (favorites.has(currentPageId)) favorites.delete(currentPageId);
    else favorites.add(currentPageId);
    state.favorites = [...favorites].slice(-MAX_FAVORITES);
    saveState();
    updateFavoriteButton();
    renderHomeState();
  }

  function applyFocusMode() {
    const active = state.preferences.focusMode === true;
    document.documentElement.dataset.focusMode = String(active);
    document.querySelectorAll("[data-cheat-focus]").forEach((button) => {
      button.setAttribute("aria-pressed", String(active));
      const text = button.querySelector("[data-cheat-button-label]");
      if (text) text.textContent = active ? "Fokus beenden" : "Fokusmodus";
    });
  }

  function toggleFocusMode(force) {
    const next = typeof force === "boolean" ? force : !state.preferences.focusMode;
    state.preferences.focusMode = next;
    saveState();
    applyFocusMode();
  }

  function currentSection() {
    return decodeURIComponent(window.location.hash.replace(/^#/, "")).slice(0, 200) || null;
  }

  function updateLastRead() {
    if (!currentPageId) return;
    state.lastRead = {
      pageId: currentPageId,
      section: currentSection(),
      updatedAt: new Date().toISOString(),
    };
    saveState();
  }

  function readingRatio() {
    const root = document.documentElement;
    const denominator = Math.max(1, root.scrollHeight - window.innerHeight);
    return Math.min(1, Math.max(0, window.scrollY / denominator));
  }

  function persistProgress(force = false) {
    if (!currentPageId) return;
    const now = Date.now();
    if (!force && now - lastProgressWrite < 500) return;
    lastProgressWrite = now;
    state.progress[currentPageId] = {
      ratio: readingRatio(),
      section: currentSection(),
      updatedAt: new Date(now).toISOString(),
    };
    saveState();
    updateProgressLabel();
  }

  function scheduleProgress() {
    if (progressFrame !== null) return;
    progressFrame = window.requestAnimationFrame(() => {
      progressFrame = null;
      persistProgress(false);
    });
  }

  function updateProgressLabel() {
    const ratio = currentPageId ? state.progress[currentPageId]?.ratio || 0 : 0;
    const percent = Math.round(ratio * 100);
    document.querySelectorAll("[data-cheat-progress]").forEach((element) => {
      element.textContent = `${percent} % gelesen`;
      element.setAttribute("aria-label", `Lesefortschritt ${percent} Prozent`);
    });
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

  function createPageLink(page, suffix = "") {
    const url = safePageUrl(page);
    if (!url) return null;
    const link = document.createElement("a");
    link.className = "cheat-local-card";
    link.href = url.href;

    const title = document.createElement("strong");
    title.textContent = page.title || "Unbenanntes Cheatsheet";
    link.append(title);

    const meta = document.createElement("span");
    const parts = [page.category_title, Number.isFinite(page.minutes) ? `ca. ${page.minutes} Min.` : null]
      .filter(Boolean);
    if (suffix) parts.push(suffix);
    meta.textContent = parts.join(" · ");
    link.append(meta);
    return link;
  }

  function renderPageCollection(container, pageIds, emptyText, suffixForPage = null) {
    if (!container) return;
    container.replaceChildren();
    const fragment = document.createDocumentFragment();
    for (const pageId of pageIds) {
      const page = pageById.get(pageId);
      const suffix = typeof suffixForPage === "function" ? suffixForPage(pageId) : "";
      const link = createPageLink(page, suffix);
      if (link) fragment.append(link);
    }
    if (!fragment.childNodes.length) {
      const empty = document.createElement("p");
      empty.className = "cheat-local-empty";
      empty.textContent = emptyText;
      fragment.append(empty);
    }
    container.append(fragment);
  }

  function renderHomeState() {
    const dashboard = document.querySelector("[data-cheat-home-state]");
    if (!dashboard) return;
    dashboard.hidden = false;

    const favoriteIds = state.favorites.filter((pageId) => pageById.has(pageId)).slice(-6).reverse();
    renderPageCollection(
      dashboard.querySelector("[data-cheat-home-favorites]"),
      favoriteIds,
      "Noch keine Favoriten gespeichert.",
    );

    const progressIds = Object.entries(state.progress)
      .filter(([pageId, entry]) => pageById.has(pageId) && entry.ratio > 0 && entry.ratio < 0.98)
      .sort((left, right) => Date.parse(right[1].updatedAt) - Date.parse(left[1].updatedAt))
      .slice(0, 6)
      .map(([pageId]) => pageId);
    renderPageCollection(
      dashboard.querySelector("[data-cheat-home-progress]"),
      progressIds,
      "Noch kein angefangener Spickzettel.",
      (pageId) => `${Math.round((state.progress[pageId]?.ratio || 0) * 100)} %`,
    );

    const lastRead = dashboard.querySelector("[data-cheat-home-last]");
    if (lastRead) {
      lastRead.replaceChildren();
      const page = state.lastRead ? pageById.get(state.lastRead.pageId) : null;
      const link = createPageLink(page, "zuletzt gelesen");
      if (link && state.lastRead?.section) {
        const url = new URL(link.href);
        url.hash = encodeURIComponent(state.lastRead.section);
        link.href = url.href;
      }
      if (link) lastRead.append(link);
      else {
        const empty = document.createElement("p");
        empty.className = "cheat-local-empty";
        empty.textContent = "Noch kein zuletzt gelesener Spickzettel.";
        lastRead.append(empty);
      }
    }
  }

  function openKeyboardHelp() {
    const dialog = document.querySelector("[data-cheat-keyboard-dialog]");
    if (!dialog) return;
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", "");
  }

  function closeKeyboardHelp() {
    const dialog = document.querySelector("[data-cheat-keyboard-dialog]");
    if (!dialog?.hasAttribute("open")) return false;
    if (typeof dialog.close === "function") dialog.close();
    else dialog.removeAttribute("open");
    return true;
  }

  function focusSearch() {
    const input = document.querySelector(
      '[data-md-component="search-query"] input, input.md-search__input',
    );
    if (!input) return false;
    input.focus();
    return true;
  }

  function isEditableTarget(target) {
    return (
      target instanceof HTMLElement &&
      (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName))
    );
  }

  function navigateTo(relativePath) {
    window.location.assign(new URL(relativePath, baseUrl()).href);
  }

  function handleShortcut(event) {
    if (!state.preferences.shortcuts || event.defaultPrevented || isEditableTarget(event.target)) {
      return;
    }
    if (event.ctrlKey || event.altKey || event.metaKey) return;

    if (event.key === "/") {
      if (focusSearch()) event.preventDefault();
      return;
    }
    if (event.key === "?") {
      event.preventDefault();
      openKeyboardHelp();
      return;
    }
    if (event.key === "Escape") {
      if (closeKeyboardHelp()) event.preventDefault();
      else if (state.preferences.focusMode) toggleFocusMode(false);
      return;
    }
    if (event.key.toLowerCase() === "f" && !event.shiftKey) {
      if (currentPageId) {
        event.preventDefault();
        toggleFavorite();
      }
      return;
    }

    const key = event.key.toLowerCase();
    if (key === "g") {
      gotoDeadline = Date.now() + GOTO_TIMEOUT_MS;
      return;
    }
    if (Date.now() > gotoDeadline) return;
    gotoDeadline = 0;
    const targets = {
      i: "index/gesamt/",
      k: "kategorien/",
      d: "downloads/",
    };
    if (targets[key]) {
      event.preventDefault();
      navigateTo(targets[key]);
    }
  }

  function bindControls() {
    const tools = pageToolRoot();
    if (tools && currentPageId) tools.hidden = false;
    document.querySelectorAll("[data-cheat-favorite]").forEach((button) => {
      button.addEventListener("click", toggleFavorite);
    });
    document.querySelectorAll("[data-cheat-focus]").forEach((button) => {
      button.addEventListener("click", () => toggleFocusMode());
    });
    document.querySelectorAll("[data-cheat-keyboard-open]").forEach((button) => {
      button.hidden = false;
      button.addEventListener("click", openKeyboardHelp);
    });
    document.querySelectorAll("[data-cheat-keyboard-close]").forEach((button) => {
      button.addEventListener("click", closeKeyboardHelp);
    });
    document.addEventListener("keydown", handleShortcut);
    window.addEventListener("scroll", scheduleProgress, { passive: true });
    window.addEventListener("hashchange", updateLastRead);
    window.addEventListener("pagehide", () => persistProgress(true));
  }

  async function initialize() {
    document.documentElement.classList.add("cheatsheets-js");
    state = loadState();
    currentPageId = readCurrentPageId();
    updateStorageNotice();

    try {
      const [pagePayload, aliasPayload] = await Promise.all([
        fetchData("pages.json"),
        fetchData("page-id-aliases.json"),
      ]);
      pages = Array.isArray(pagePayload) ? pagePayload : [];
      pageById = new Map(
        pages.filter((page) => isPageId(page?.id)).map((page) => [page.id, page]),
      );
      migrateState(aliasPayload);
    } catch (error) {
      console.warn("Lokale Cheatsheet-Daten konnten nicht geladen werden.", error);
    }

    applyFocusMode();
    bindControls();
    updateFavoriteButton();
    updateLastRead();
    persistProgress(true);
    renderHomeState();
    document.documentElement.dataset.cheatsheetUi = "ready";
    document.dispatchEvent(new CustomEvent("cheatsheets:ui-ready"));
  }

  window.CheatsheetsUI = Object.freeze({
    storageKey: STORAGE_KEY,
    toggleFavorite,
    toggleFocusMode,
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }
})();
