(() => {
  "use strict";

  const STORAGE_KEY = "cheatsheets.ui.v1";
  const SCHEMA_VERSION = 1;

  function readState() {
    try {
      const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
      if (!parsed || parsed.schema !== SCHEMA_VERSION || typeof parsed !== "object") {
        return {
          schema: SCHEMA_VERSION,
          favorites: [],
          lastRead: null,
          progress: {},
          preferences: { focusMode: false, shortcuts: true },
        };
      }
      parsed.preferences = {
        focusMode: parsed.preferences?.focusMode === true,
        shortcuts: parsed.preferences?.shortcuts !== false,
      };
      return parsed;
    } catch {
      return null;
    }
  }

  function bindShortcutPreference() {
    const toggles = document.querySelectorAll("[data-cheat-shortcuts-toggle]");
    if (!toggles.length) return;
    const state = readState();
    if (!state) {
      toggles.forEach((toggle) => {
        toggle.checked = true;
        toggle.disabled = true;
        toggle.title = "Lokale Speicherung ist in diesem Browser nicht verfügbar.";
      });
      return;
    }

    toggles.forEach((toggle) => {
      toggle.checked = state.preferences.shortcuts;
      toggle.addEventListener("change", () => {
        const current = readState();
        if (!current) {
          toggle.checked = true;
          toggle.disabled = true;
          return;
        }
        current.preferences.shortcuts = toggle.checked;
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(current));
          window.location.reload();
        } catch {
          toggle.checked = true;
          toggle.disabled = true;
        }
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindShortcutPreference, { once: true });
  } else {
    bindShortcutPreference();
  }
})();
