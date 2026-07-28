(() => {
  "use strict";

  const STORAGE_KEY = "cheatsheets.ui.v1";
  const SCHEMA_VERSION = 1;
  const MAX_FAVORITES = 100;
  const MAX_PROGRESS_ENTRIES = 200;
  const GOTO_TIMEOUT_MS = 1500;

  let storageAvailable = true;
  let state = emptyState();
  let pageById = new Map();
  let currentPageId = null;
  let gotoDeadline = 0;
  let progressFrame = null;
  let lastProgressWrite = 0;

  function emptyState() {
    return {
      schema: SCHEMA_VERSION,
      favorites: [],
      lastRead: null,
      progress: {},
      preferences: { focusMode: false, shortcuts: true },
    };
  }

  function isObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

  function isPageId(value) {
    return typeof value === "string" && /^p_[0-9a-f]{16}$/.test(value);
  }

  function validTimestamp(value) {
    if (typeof value !== "string" || !Number.isFinite(Date.parse(value))) return null;
    return new Date(Date.parse(value)).toISOString();
  }

  function normalizedProgress(value) {
    if (!isObject(value)) return null;
    const ratio = Number(value.ratio);
    const updatedAt = validTimestamp(value.updatedAt);
    if (!Number.isFinite(ratio) || !updatedAt) return null;
    return {
      ratio: Math.min(1, Math.max(0, ratio)),
      section: typeof value.section === "string" ? value.section.slice(0, 200) : null,
      updatedAt,
    };
  }

  function normalizeState(value) {
    const result = emptyState();
    if (!isObject(value) || value.schema !== SCHEMA_VERSION) return result;

    if (Array.isArray(value.favorites)) {
      result.favorites = [...new Set(value.favorites.filter(isPageId))].slice(
        0,
        MAX_FAVORITES,
      );
    }

    if (isObject(value.lastRead) && isPageId(value.lastRead.pageId)) {
      const updatedAt = validTimestamp(value.lastRead.updatedAt);
      if (updatedAt) {
        result.lastRead = {
          pageId: value.lastRead.pageId,
          section:
            typeof value.lastRead.section === "string"
              ? value.lastRead.section.slice(0, 200)
              : null,
          updatedAt,
        };
      }
    }

    if (isObject(value.progress)) {
      const entries = Object.entries(value.progress)
        .filter(([pageId]) => isPageId(pageId))
        .map(([pageId, entry]) => [pageId, normalizedProgress(entry)])
        .filter(([, entry]) => entry !== null)
        .sort((left, right) => Date.parse(right[1].updatedAt) - Date.parse(left[1].updatedAt))
        .slice(0, MAX_PROGRESS_ENTRIES);
      result.progress = Object.fromEntries(entries);
    }

    if (isObject(value.preferences)) {
      result.preferences.focusMode = value.preferences.focusMode === true;
      result.preferences.shortcuts = value.preferences.shortcuts !== false;
    }
    return result;
  }

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return normalizeState(raw ? JSON.parse(raw) : null);
    } catch {
      storageAvailable = false;
      return emptyState();
    }
  }

  function saveState() {
    if (!storageAvailable) return false;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      return true;
    } catch {
      storageAvailable = false;
      updateStorageControls();
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

  function migrateState(payload) {
    const aliases = isObject(payload?.aliases) ? payload.aliases : {};
    let changed = false;

    const favorites = [
      ...new Set(state.favorites.map((pageId) => migrateId(pageId, aliases))),
    ].filter(isPageId);
    if (JSON.stringify(favorites) !== JSON.stringify(state.favorites)) changed = true;
    state.favorites = favorites.slice(0, MAX_FAVORITES);

    if (state.lastRead) {
      const migrated = migrateId(state.lastRead.pageId, aliases);
      changed ||= migrated !== state.lastRead.pageId;
      state.lastRead.pageId = migrated;
    }

    const progress = {};
    for (const [pageId, entry] of Object.entries(state.progress)) {
      const migrated = migrateId(pageId, aliases);
      changed ||= migrated !== pageId;
      const existing = progress[migrated];
      if (!existing || Date.parse(entry.updatedAt) > Date.parse(existing.updatedAt)) {
        progress[migrated] = entry;
      }
    }
    state.progress = progress;
    if (changed) saveState();
  }

  function toolRoot() {
    return document.querySelector("[data-cheatsheet-page-tools]");
  }

  function readCurrentPageId() {
    const value = toolRoot()?.dataset.pageId || "";
    return isPageId(value) ? value : null;
  }

  function updateStorageControls() {
    document.documentElement.dataset.cheatsheetStorage = storageAvailable
      ? "available"
      : "unavailable";
    document.querySelectorAll("[data-cheat-storage-note]").forEach((element) => {
      element.hidden = storageAvailable;
    });
    document.querySelectorAll("[data-cheat-shortcuts-toggle]").forEach((toggle) => {
      toggle.disabled = !storageAvailable;
      toggle.title = storageAvailable
        ? ""
        : "Lokale Speicherung ist in diesem Browser nicht verfügbar.";
    });
  }

  function updateFavoriteButtons() {
    const active = Boolean(currentPageId && state.favorites.includes(currentPageId));
    document.querySelectorAll("[data-cheat-favorite]").forEach((button) => {
      button.setAttribute("aria-pressed", String(active));
      button.dataset.active = String(active);
      button.setAttribute(
        "aria-label",
        active ? "Aus Favoriten entfernen" : "Zu Favoriten hinzufügen",
      );
      const label = button.querySelector("[data-cheat-button-label]");
      if (label) label.textContent = active ? "Favorit" : "Merken";
    });
  }

  function toggleFavorite() {
    if (!currentPageId) return;
    const favorites = new Set(state.favorites);
    if (favorites.has(currentPageId)) favorites.delete(currentPageId);
    else favorites.add(currentPageId);
    state.favorites = [...favorites].slice(-MAX_FAVORITES);
    saveState();
    updateFavoriteButtons();
    renderHomeState();
  }

  function applyFocusMode() {
    const active = state.preferences.focusMode === true;
    document.documentElement.dataset.focusMode = String(active);
    document.querySelectorAll("[data-cheat-focus]").forEach((button) => {
      button.setAttribute("aria-pressed", String(active));
      const label = button.querySelector("[data-cheat-button-label]");
      if (label) label.textContent = active ? "Fokus beenden" : "Fokusmodus";
    });
  }

  function setFocusMode(value) {
    state.preferences.focusMode = Boolean(value);
    saveState();
    applyFocusMode();
  }

  function toggleFocusMode() {
    setFocusMode(!state.preferences.focusMode);
  }

  function updateShortcutControls() {
    document.querySelectorAll("[data-cheat-shortcuts-toggle]").forEach((toggle) => {
      toggle.checked = state.preferences.shortcuts;
    });
  }

  function setShortcutsEnabled(value) {
    state.preferences.shortcuts = Boolean(value);
    saveState();
    updateShortcutControls();
  }

  function currentSection() {
    const raw = window.location.hash.replace(/^#/, "").slice(0, 400);
    if (!raw) return null;
    try {
      return decodeURIComponent(raw).slice(0, 200) || null;
    } catch {
      return raw.slice(0, 200) || null;
    }
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
    const denominator = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
    return Math.min(1, Math.max(0, window.scrollY / denominator));
  }

  function pruneProgress() {
    state.progress = Object.fromEntries(
      Object.entries(state.progress)
        .sort((left, right) => Date.parse(right[1].updatedAt) - Date.parse(left[1].updatedAt))
        .slice(0, MAX_PROGRESS_ENTRIES),
    );
  }

  function updateProgressLabel() {
    const ratio = currentPageId ? state.progress[currentPageId]?.ratio || 0 : 0;
    const percent = Math.round(ratio * 100);
    document.querySelectorAll("[data-cheat-progress]").forEach((element) => {
      element.textContent = `${percent} % gelesen`;
      element.setAttribute("aria-label", `Lesefortschritt ${percent} Prozent`);
    });
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
    pruneProgress();
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

  function safePageUrl(page) {
    if (!page || typeof page.url !== "string") return null;
    try {
      const url = new URL(page.url, baseUrl());
      return url.origin === window.location.origin ? url : null;
    } catch {
      return null;
    }
  }

  function pageCard(page, suffix = "") {
    const url = safePageUrl(page);
    if (!url) return null;
    const link = document.createElement("a");
    link.className = "cheat-local-card";
    link.href = url.href;

    const title = document.createElement("strong");
    title.textContent = page.title || "Unbenanntes Cheatsheet";
    link.append(title);

    const meta = document.createElement("span");
    const parts = [
      page.category_title,
      Number.isFinite(page.minutes) ? `ca. ${page.minutes} Min.` : null,
      suffix || null,
    ].filter(Boolean);
    meta.textContent = parts.join(" · ");
    link.append(meta);
    return link;
  }

  function renderCollection(container, pageIds, emptyText, suffixForPage = null) {
    if (!container) return;
    container.replaceChildren();
    const fragment = document.createDocumentFragment();
    for (const pageId of pageIds) {
      const suffix = typeof suffixForPage === "function" ? suffixForPage(pageId) : "";
      const link = pageCard(pageById.get(pageId), suffix);
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

    const favorites = state.favorites
      .filter((pageId) => pageById.has(pageId))
      .slice(-6)
      .reverse();
    renderCollection(
      dashboard.querySelector("[data-cheat-home-favorites]"),
      favorites,
      "Noch keine Favoriten gespeichert.",
    );

    const progressIds = Object.entries(state.progress)
      .filter(([pageId, entry]) => pageById.has(pageId) && entry.ratio > 0 && entry.ratio < 0.98)
      .sort((left, right) => Date.parse(right[1].updatedAt) - Date.parse(left[1].updatedAt))
      .slice(0, 6)
      .map(([pageId]) => pageId);
    renderCollection(
      dashboard.querySelector("[data-cheat-home-progress]"),
      progressIds,
      "Noch kein angefangener Spickzettel.",
      (pageId) => `${Math.round((state.progress[pageId]?.ratio || 0) * 100)} %`,
    );

    const last = dashboard.querySelector("[data-cheat-home-last]");
    if (!last) return;
    last.replaceChildren();
    const page = state.lastRead ? pageById.get(state.lastRead.pageId) : null;
    const link = pageCard(page, "zuletzt gelesen");
    if (link && state.lastRead?.section) {
      const url = new URL(link.href);
      url.hash = encodeURIComponent(state.lastRead.section);
      link.href = url.href;
    }
    if (link) last.append(link);
    else {
      const empty = document.createElement("p");
      empty.className = "cheat-local-empty";
      empty.textContent = "Noch kein zuletzt gelesener Spickzettel.";
      last.append(empty);
    }
  }

  function keyboardDialog() {
    return document.querySelector("[data-cheat-keyboard-dialog]");
  }

  function openKeyboardHelp() {
    const dialog = keyboardDialog();
    if (!dialog || dialog.hasAttribute("open")) return;
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", "");
  }

  function closeKeyboardHelp() {
    const dialog = keyboardDialog();
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

  function isEditable(target) {
    return (
      target instanceof HTMLElement &&
      (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName))
    );
  }

  function navigateTo(path) {
    window.location.assign(new URL(path, baseUrl()).href);
  }

  function handleShortcut(event) {
    if (!state.preferences.shortcuts || event.defaultPrevented || isEditable(event.target)) return;
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
      else if (state.preferences.focusMode) setFocusMode(false);
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
    const targets = { i: "index/gesamt/", k: "kategorien/", d: "downloads/" };
    if (targets[key]) {
      event.preventDefault();
      navigateTo(targets[key]);
    }
  }

  function bindControls() {
    const tools = toolRoot();
    if (tools && currentPageId) tools.hidden = false;
    document.querySelectorAll("[data-cheat-favorite]").forEach((button) => {
      button.addEventListener("click", toggleFavorite);
    });
    document.querySelectorAll("[data-cheat-focus]").forEach((button) => {
      button.addEventListener("click", toggleFocusMode);
    });
    document.querySelectorAll("[data-cheat-keyboard-open]").forEach((button) => {
      button.hidden = false;
      button.addEventListener("click", openKeyboardHelp);
    });
    document.querySelectorAll("[data-cheat-keyboard-close]").forEach((button) => {
      button.addEventListener("click", closeKeyboardHelp);
    });
    document.querySelectorAll("[data-cheat-shortcuts-toggle]").forEach((toggle) => {
      toggle.addEventListener("change", () => setShortcutsEnabled(toggle.checked));
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
    updateStorageControls();

    try {
      const [pagePayload, aliasPayload] = await Promise.all([
        fetchData("pages.json"),
        fetchData("page-id-aliases.json"),
      ]);
      const pages = Array.isArray(pagePayload) ? pagePayload : [];
      pageById = new Map(
        pages.filter((page) => isPageId(page?.id)).map((page) => [page.id, page]),
      );
      migrateState(aliasPayload);
    } catch (error) {
      console.warn("Lokale Cheatsheet-Daten konnten nicht geladen werden.", error);
    }

    applyFocusMode();
    updateShortcutControls();
    bindControls();
    updateFavoriteButtons();
    updateLastRead();
    persistProgress(true);
    renderHomeState();
    document.documentElement.dataset.cheatsheetUi = "ready";
    document.dispatchEvent(new CustomEvent("cheatsheets:ui-ready"));
  }

  window.CheatsheetsUI = Object.freeze({
    setShortcutsEnabled,
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
