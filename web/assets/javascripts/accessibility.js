(() => {
  "use strict";

  function enhanceScrollableRegions() {
    const selectors = [
      [".md-typeset__table", "Horizontal scrollbare Tabelle"],
      [".md-typeset pre", "Horizontal scrollbarer Codeblock"],
    ];

    for (const [selector, label] of selectors) {
      document.querySelectorAll(selector).forEach((element, index) => {
        if (!element.hasAttribute("tabindex")) element.tabIndex = 0;
        if (!element.hasAttribute("aria-label")) {
          element.setAttribute("aria-label", `${label} ${index + 1}`);
        }
      });
    }
  }

  function isEditable(target) {
    return (
      target instanceof HTMLElement &&
      (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName))
    );
  }

  function keyboardHelpEnabled() {
    const toggle = document.querySelector("[data-cheat-shortcuts-toggle]");
    return !toggle || toggle.checked;
  }

  function openKeyboardHelpFromCapture(event) {
    const helpKey = event.key === "?" || (event.key === "/" && event.shiftKey);
    if (
      !helpKey ||
      event.ctrlKey ||
      event.altKey ||
      event.metaKey ||
      isEditable(event.target) ||
      !keyboardHelpEnabled()
    ) {
      return;
    }

    const dialog = document.querySelector("[data-cheat-keyboard-dialog]");
    if (!dialog || dialog.hasAttribute("open")) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", "");
  }

  document.addEventListener("keydown", openKeyboardHelpFromCapture, {
    capture: true,
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", enhanceScrollableRegions, {
      once: true,
    });
  } else {
    enhanceScrollableRegions();
  }

  document.addEventListener("cheatsheets:ui-ready", enhanceScrollableRegions);
})();
